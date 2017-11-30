# -*- coding: utf-8 -*-
"""
    This file is part of OctoCamDox

    OctoCamDox is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OctoCamDox is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OctoCamDox.  If not, see <http://www.gnu.org/licenses/>.

    Main author: Dennis Struhs <dennis.struhs@hamburg.de>
"""

from __future__ import absolute_import


import octoprint.plugin
import flask
import re
from subprocess import call
import os
import time
import datetime
import base64
import shutil
import json
import struct
import imghdr

import cv2
import numpy as np

import time
import datetime

from copy import deepcopy
from collections import deque

from .GCode_processor import CameraGCodeExtraction as GCodex
from .GCode_processor import CustomJSONEncoder as CoordJSONify
from .GCode_processor import Coordinate
from .CameraCoordinateGetter import CameraGridMaker as CGridmaker
from .CameraCoordsWithOptions import CameraGridMakerWithOptions as CGridWithOpts
from .image_merger import ImageMerger as imerge
from .image_mergerWithOptions import ImageMergerWithOptions as imergeOpts


__plugin_name__ = "OctoCamDox"
__plugin_version__ = "0.9"

#instantiate plugin object and register hook for gcode injection
def __plugin_load__():

    octocamdox = OctoCamDox()

    global __plugin_implementation__
    __plugin_implementation__ = octocamdox

    global __plugin_hooks__
    __plugin_hooks__ = {'octoprint.comm.protocol.gcode.queuing': octocamdox.hook_gcode_queuing}


class OctoCamDox(octoprint.plugin.StartupPlugin,
            octoprint.plugin.TemplatePlugin,
            octoprint.plugin.EventHandlerPlugin,
            octoprint.plugin.SettingsPlugin,
            octoprint.plugin.AssetPlugin,
            octoprint.plugin.SimpleApiPlugin,
            octoprint.plugin.BlueprintPlugin):

    FEEDRATE = 4000.000


    def __init__(self):
        self._currentZ = None
        self.GCoordsList = []
        self.CameraGridCoordsList = []
        self.GridInfoList = []
        self.currentLayer = 0

        self.fileUploadPath = None
        self.cameraImagePath = None
        self.qeue = None
        self.qelem = None

        self.CamPixelX = None
        self.CamPixelY = None

        self.our_pic_width = None
        self.our_pic_height = None

        self.currentPrintJobDir = None #Holds the current printjob folder dir

        self.mode = "normal" #Contains the mode for the camera callback

        self.ImageArray = [] #Stores the incoming images in an array
        self.MergedImage = None #Is created by stitching the tile images together

        self.M942IgnoredTimes = 0 #Used to ignore the first M942 command

    def on_after_startup(self):
    #     self.imgproc = ImageProcessing(
    #         float(self._settings.get(["tray", "boxsize"])),
    #         int(self._settings.get(["camera", "bed", "binary_thresh"])),
    #         int(self._settings.get(["camera", "head", "binary_thresh"])))
    #     #used for communication to UI
        self._pluginManager = octoprint.plugin.plugin_manager()

    # Add helpers from the auxilary OctoPNP plug-in to grab images and camera resolution
	helpers = self._pluginManager.get_helpers("OctoPNP", "get_head_camera_image", "get_head_camera_pxPerMM")
        if helpers and "get_head_camera_image" in helpers:
            self.get_camera_image = helpers["get_head_camera_image"]
        if helpers and "get_head_camera_pxPerMM" in helpers:
            self.get_camera_resolution = helpers["get_head_camera_pxPerMM"]

    def on_settings_save(self, data):
        # If any change was made to the settings, update the grid
        if(self.settingsHaveChanged(data)):
            self._handleGridCreation()

    def get_settings_defaults(self):
        return dict(target_folder = "",
                    layer_height = 0.25,
                    target_extruder = "",
                    picture_width = 800,
                    picture_height = 800,
                    normalMode = "on",
                    forceRTL = "off",
                    forceLTR = "off",
                    addSlipFlaps = False,
                    activateCamGrab = True)

    def get_template_configs(self):
        return [
            dict(type="tab", template="OctoCamDox_tab.jinja2"),
            dict(type="settings", template="OctoCamDox_settings.jinja2")
            #dict(type="settings", custom_bindings=True)
        ]

    def get_assets(self):
        return dict(
            js=["js/OctoCamDox.js",
                "js/camGrid.js",
                "js/settings.js"]
        )

    def get_api_commands(self):
        return dict(
            getImageResolution=[],
        )

    def on_api_get(self, request):
        self.mode = "resolution_get"
        self._setNewGridResolution()
        # As long as the variables are not here, send python to sleep
        while(self.our_pic_width is None or self.our_pic_height is None):
            time.sleep(1)
        return flask.jsonify(width = self.our_pic_width,
                             height = self.our_pic_height)

    # Use the on_event hook to extract XML data every time a new file has been loaded by the user
    def on_event(self, event, payload):
        #extraxt part informations from inline xmly
        if event == "FileSelected":
            #Retrieve the dirs for the GCode uploads using the filemanager
            try:
                self.fileUploadPath = self._file_manager.path_on_disk(payload.get("origin"), payload.get("path"))
            except NoSuchstorage:
                self._logger.info("ERROR - File was on a SD card, reading was not possible!")
            except io.UnsupportedOperation:
                self._logger.info("ERROR - No files are available!")

            # Start the necessary grid creation routines if all went well
            self._handleGridCreation()

            self._logger.info("Created the camera lookup grid succesfully from the file: %s", payload.get("file"))
            self._logger.info( "Current Target folder setting is: %s", self._settings.get(["target_folder"]))

        # Create new Folder for dropping the images for the new printjob
        if(event == "PrintStarted"):
            # Reset the values for each new printjob
            self.ImageArray = []
            self.MergedImage = None
            self.currentLayer = 0
            self.M942IgnoredTimes = 0
            # Create a new folder for the incoming images
            self.currentPrintJobDir = self.getBasePath()
            os.mkdir(self.currentPrintJobDir)

    """
    This function handles all necessary actions to create the camera lookup grid
    """
    def _handleGridCreation(self):
        #Reset values just in case another file was loaded before
        self.resetValues()
        # Get the necessary values from the settings tab
        layerHeight = self._settings.get_int(["layer_height"])
        targetExtruder = self._settings.get(["target_extruder"])
        #Initilize the Cameraextractor Class
        newCamExtractor = GCodex(layerHeight,targetExtruder)

        f = self._openGCodeFiles(self.fileUploadPath)

        #Extract the GCodes for the CameraPath Algortihm
        newCamExtractor.extractCameraGCode(f)
        self.GCoordsList = newCamExtractor.getCoordList()

        #Get the values for the Camera grid box sizes
        self._computeLookupGridValues()

        #Now create the actual grid
        self._createCameraGrid(
            self.GCoordsList,
            self.CamPixelX,
            self.CamPixelY)

        # Now update the canvas with the new data
        self._updateUI("FILE", "")

    def _createCameraGrid(self,inputList,CamResX,CamResY):
        templist = []
        infoList = []
        count = 0
        while count < len(inputList):
            #Creates a new CGridmaker Object with int Numbers for the Cam resolution
            if(self._settings.get(["forceRTL"]) == 'on' or self._settings.get(["forceLTR"]) == 'on'):
                newGridMaker = CGridWithOpts(self._settings,inputList,count,CamResX,CamResY)
            else:
                newGridMaker = CGridmaker(inputList,count,CamResX,CamResY)

            #Execute all necessary operations to create the actual CameraGrid
            newGridMaker.getCoordinates()
            newGridMaker.createCameraLookUpGrid()
            newGridMaker.optimizeGrid()
            if(self._settings.get(["addSlipFlaps"])):
                newGridMaker.addSlipFlaps()

            infoList.append([newGridMaker.getMaxX(),
                    newGridMaker.getMinX(),
                    newGridMaker.getMaxY(),
                    newGridMaker.getMinY(),
                    newGridMaker.getCenterX(),
                    newGridMaker.getCenterY(),
                    newGridMaker.getRows()])
            templist.append(newGridMaker.getCameraCoords())
            count += 1

        # Retrieve the necessary variables to be forwarded to the Octoprint Canvas
        self.CameraGridCoordsList = templist
        self.GridInfoList = infoList
        # Retrieve the info about how many tile rows exist for image stitching
#------------------------------------------------------------------------------
    """
    Use the gcode hook to start the camera grid documentation processes.
    """
    def hook_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if "M942" in cmd:
            if(self._settings.get(["activateCamGrab"]) is True):
                # HACK: Workaround to ignore one M942 command
                if(self.M942IgnoredTimes >= 1):
                    #Stop printing process to prevent new GCodes to be send
                    if(self._printer.is_printing()):
                        self._printer.pause_print()
                    self._logger.info( "Qeued command to start the Camera documentation" )

                    # Get current Z Position
                    if self._printer.get_current_data()["currentZ"]:
                        self._currentZ = float(self._printer.get_current_data()["currentZ"])
                    else:
                        self._currentZ = 0.0

                    # Create the qeue for the printer camera coordinates
                    self.invertYCoordinates() #Invert the Y coordinates for the printer
                    self.qeue = deque(self.CameraGridCoordsList[self.currentLayer])
                    self.qelem = self.getNewQeueElem()
                    # Decide if only movement is necessary or actual picture capturing
                    if(self.qelem):
                        self.get_camera_image(self.qelem.x, self.qelem.y, self.get_camera_image_callback, True)
                # Increment M942IgnoredTimes
                self.M942IgnoredTimes += 1
            return "G4 P1" # return dummy command

    	if "M945" in cmd:
    	    self.currentPrintJobDir = self.getBasePath()
            os.mkdir(self.currentPrintJobDir)
    """
    Implementation of the callback function to actually perform the image
    capturing, based on the injected M942 code.
    """
    def get_camera_image_callback(self, path):
    	print "Returned image path was: "
    	print path
        self.cameraImagePath = path
        print("Entered image processing callback")

        # Get the picture for the grid tiles here
        if(self.mode == "normal"):
            if(self.qelem.mode != "walk"):
                # Copy found files over to the target destination folder
                self.copyImageFiles(self.cameraImagePath)
            # Get new element and continue tacking pictures if qeue not empty
            self.qelem = self.getNewQeueElem()
            if(self.qelem):
                self.get_camera_image(self.qelem.x, self.qelem.y, self.get_camera_image_callback, False)

        # Get the resolution for the settings button here
        if(self.mode == "resolution_get"):
            self.our_pic_width,self.our_pic_height = self._get_image_size(self.cameraImagePath)
            self._logger.info("The found image resolution was: %dx%d",self.our_pic_width,self.our_pic_width)
            self.mode = "normal" # Return to normal mode after finishing
    """
    Returns the next element that the camera should goto in order to take images
    """
    def getNewQeueElem(self):
        #While the qeue still contains elements, return them.
        #Else prepare for next layer.
        if(self.qeue):
            return self.qeue.popleft()
        else:
            #Start stitching images when qeue is empty
            self.handleImages()
            self.currentLayer += 1 #Finally Increment layer when qeue was empty
            #Resume printing process after all Images have been taken
            if(self._printer.is_paused()):
                self._printer.resume_print()
            return(None)

    # def _handleCameraActions(self,elem):
    #     if(elem.mode == "walk"):
    #         # Only move printer head to position
    #         self._moveCameraToCamGrid(elem.x,elem.y)
    #         # Get new item from the Qeue and capture an image
    #         elem = self.getNewQeueElem()
    #         if(elem):
    #             self.get_camera_image(elem.x, elem.y, self.get_camera_image_callback, False)
    #     else:
    #         self.get_camera_image(elem.x, elem.y, self.get_camera_image_callback, False)

#------------------------------------------------------------------------------

    """Copies each image captured by the printer camera
    :param srcpath: Contains the absolute path to the target file"""
    def copyImageFiles(self, srcpath):
        self._logger.info( "Fetch Image from: %s", srcpath )
        self.ImageArray.append(cv2.imread(srcpath))

    def handleImages(self):
        if(not(self._settings.get(["forceRTL"]) == "on" or self._settings.get(["forceLTR"]) == "on")):
            ImageMerger = imerge(self.ImageArray,self.GridInfoList[self.currentLayer][6])
            ImageMerger.mergeImages()
        else:
            ImageMerger = imergeOpts(self._settings,
            self.ImageArray,self.GridInfoList[self.currentLayer][6])
            ImageMerger.mergeImages()
        # Hand over the results to the target dir and cleanup the Image array
        self.MergedImage = ImageMerger.get_MergedImage()
        self.writeImage("png") #Write files when ready!
        self.ImageArray = [] #Clear ImageArray for next round

    def writeImage(self, suffix):
        cv2.imwrite(self.getProperTargetPathName(suffix), self.MergedImage)

    def getProperTargetPathName(self,filesuffix):
        return os.path.join(self.currentPrintJobDir, 'Layer_{}'.format(self.currentLayer) + '.' + filesuffix)

    def getBasePath(self):
        return os.path.join(self._settings.get(["target_folder"]), 'Printjob_{}'.format(self.getTimeStamp()))

    def getTimeStamp(self):
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d__%H'+'h'+'_%M'+'m'+'_%S'+'s')
        return timestamp

    """
    Invert the Y coordinates for the printer.
    """
    def invertYCoordinates(self):
        inputlist = self.CameraGridCoordsList[self.currentLayer]
        centerY = self.GridInfoList[self.currentLayer][5]
        tempList = []
        index = 0
        while(index < len(inputlist)):
            delta = (inputlist[index].y - centerY)*2
            newpos = inputlist[index].y - delta
            newCoord = Coordinate(inputlist[index].x, newpos)
            newCoord.set_mode(inputlist[index].mode)
            tempList.append(newCoord)
            index += 1
        self.CameraGridCoordsList[self.currentLayer] = deepcopy(tempList)

    def _openGCodeFiles(self, inputName):
        gcode = open( inputName, 'r' )
        readData = gcode.readlines()
        gcode.close()
        return readData

    def _moveCameraToCamGrid(self ,Xpos ,Ypos):
        # move camera to part position
        cmd = "G1 X" + str(Xpos) + " Y" + str(Ypos) + " F" + str(self.FEEDRATE)
        self._logger.info("Move camera to: %s , %s",Xpos,Ypos)
        self._printer.commands(cmd)

    """This function sets up the necessary values for the camera lookup grid steps,
    by taking a sample picture at a certain point."""
    def _setNewGridResolution(self):
        # Get an image to determine the camera resolution
        self.get_camera_image(0, 0, self.get_camera_image_callback, True)

    def _computeLookupGridValues(self):
        PixelPerMillimeter = self.get_camera_resolution("HEAD")
        # Divide the resolution by the PixelPerMillimeter ratio
        self.CamPixelX = self._settings.get_int(["picture_width"]) / PixelPerMillimeter["x"]
        self.CamPixelY = self._settings.get_int(["picture_height"]) / PixelPerMillimeter["y"]

    """This function retrieves the resolution of the .png, .gif or .jpeg image file passed into it.
    This function was copypasted from https://stackoverflow.com/questions/8032642/how-to-obtain-image-size-using-standard-python-class-without-using-external-lib
    :param fname: Contains the filename of the file """
    def _get_image_size(self, fname):
        with open(fname, 'rb') as fhandle:
            head = fhandle.read(24)
            if len(head) != 24:
                return
            if imghdr.what(fname) == 'png':
                check = struct.unpack('>i', head[4:8])[0]
                if check != 0x0d0a1a0a:
                    return
                width, height = struct.unpack('>ii', head[16:24])
            elif imghdr.what(fname) == 'gif':
                width, height = struct.unpack('<HH', head[6:10])
            elif imghdr.what(fname) == 'jpeg':
                try:
                    fhandle.seek(0) # Read 0xff next
                    size = 2
                    ftype = 0
                    while not 0xc0 <= ftype <= 0xcf:
                        fhandle.seek(size, 1)
                        byte = fhandle.read(1)
                        while ord(byte) == 0xff:
                            byte = fhandle.read(1)
                        ftype = ord(byte)
                        size = struct.unpack('>H', fhandle.read(2))[0] - 2
                    # We are at a SOFn block
                    fhandle.seek(1, 1)  # Skip `precision' byte.
                    height, width = struct.unpack('>HH', fhandle.read(4))
                except Exception: #IGNORE:W0703
                    return
            else:
                return
            return width, height

    def resetValues(self):
        self._currentZ = None
        self.GCoordsList = []
        self.CameraGridCoordsList = []
        self.GridInfoList = []
        self.currentLayer = 0
        self.cameraImagePath = None
        self.qeue = None
        self.CamPixelX = None
        self.CamPixelY = None
        self.our_pic_width = None
        self.our_pic_height = None
        self.currentPrintJobDir = None
        self.mode = "normal"
        self.ImageArray = []
        self.MergedImage = None
        self.M942IgnoredTimes = 0

    """
    Refactored method to return a lengthy boolean function
    """
    def settingsHaveChanged(self, data):
        settingsObj = octoprint.plugin.SettingsPlugin
        return (settingsObj.on_settings_save(self, data) is not None
        and self.fileUploadPath is not None)

    def _updateUI(self, event, parameter):
        data = dict(
            info="dummy"
        )
        if (event == "FILE"):
            if (self.GCoordsList != None):
                # compile part information
                data = dict(
                    gcodeCoordinates = json.dumps(self.GCoordsList,cls=CoordJSONify),
                    cameraCoordinates = json.dumps(self.CameraGridCoordsList,cls=CoordJSONify),
                    gridInfoList = json.dumps(self.GridInfoList,cls=CoordJSONify),
                    CamPixelResX = self.CamPixelX,
                    CamPixelResY = self.CamPixelY,
                )
        elif event is "HEADIMAGE":
            # open image and convert to base64
            f = open(parameter,"r")
            data = dict(
                src = "data:image/" + os.path.splitext(parameter)[1] + ";base64,"+base64.b64encode(bytes(f.read()))
            )

        message = dict(
            event=event,
            data=data
        )
        self._pluginManager.send_plugin_message(__plugin_name__, message)
