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

from .GCode_processor import CameraGCodeExtraction as GCodex
from .GCode_processor import CustomJSONEncoder as CoordJSONify
from .CameraCoordinateGetter import CameraGridMaker


__plugin_name__ = "OctoCamDox"

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

        self.cameraImagePath = None

        self.CamPixelX = None
        self.CamPixelY = None


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
            self._logger.info("FOUND HELPER FOR TAKING IMAGE!!!")
            self.get_camera_image = helpers["get_head_camera_image"]
        if helpers and "get_head_camera_pxPerMM" in helpers:
            self._logger.info("FOUND HELPER FOR CAMERARESOLUTION!!!")
            self.get_camera_resolution = helpers["get_head_camera_pxPerMM"]


    def get_settings_defaults(self):
        return {
            #"publicHost": None,
            #"publicPort": None,
            "tray": {
                "x": 0,
                "y": 0,
                "z": 0,
                "rows" : 5,
                "columns": 5,
                "boxsize": 10,
                "rimsize": 1.0
            },
            "vacnozzle": {
                "x": 0,
                "y": 0,
                "z_pressure": 0,
                "extruder_nr": 2,
                "grip_vacuum_gcode": "M340 P0 S1200",
                "release_vacuum_gcode": "M340 P0 S1500",
                "lower_nozzle_gcode": "",
                "lift_nozzle_gcode": ""
            },
            "camera": {
                "head": {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "path": "",
                    "binary_thresh": 150,
                    "grabScriptPath": ""
                },
                "bed": {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "pxPerMM": 50.0,
                    "path": "",
                    "binary_thresh": 150,
                    "grabScriptPath": ""
                },
                "image_logging": False
            }
        }

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

    # Use the on_event hook to extract XML data every time a new file has been loaded by the user
    def on_event(self, event, payload):
        #extraxt part informations from inline xmly
        if event == "FileSelected":
            #Initilize the Cameraextractor Class
            newCamExtractor = GCodex(0.25,'T0')
            #Retrieve the basefolder for the GCode uploads
            uploadsPath = self._settings.global_get_basefolder("uploads") + "\\" + payload.get("path")

            f = self._openGCodeFiles(uploadsPath)
            #f = open(testPath, 'r')

            #Extract the GCodes for the CameraPath Algortihm
            newCamExtractor.extractCameraGCode(f)

            self.GCoordsList = newCamExtractor.getCoordList()

            #Get the values for the Camera grid box sizes
            self._getAndSetGridResolution()

            self._createCameraGrid(
                self.GCoordsList,
                self.CamPixelX,
                self.CamPixelY)

            self._logger.info("Created the camera lookup grid succesfully from the file: %s", payload.get("file"))
            self._updateUI("FILE", "")


    def _createCameraGrid(self,inputList,CamResX,CamResY):
        templist = []
        infoList = []
        count = 0
        while count < len(inputList):
            #Creates a new CameraGridMaker Object with int Numbers for the Cam resolution
            newGridMaker = CameraGridMaker(inputList,count,CamResX,CamResY)

            #Execute all necessary operations to create the actual CameraGrid
            newGridMaker.getCoordinates()
            newGridMaker.createCameraLookUpGrid()

            infoList.append([newGridMaker.getMaxX(),
                    newGridMaker.getMinX(),
                    newGridMaker.getMaxY(),
                    newGridMaker.getMinY(),
                    newGridMaker.getCenterX(),
                    newGridMaker.getCenterY()])
            templist.append(newGridMaker.getCameraCoords())
            count += 1

        #Retrieve the necessary variables to be forwarded to the Octoprint Canvas
        self.CameraGridCoordsList = templist
        self.GridInfoList = infoList


    """
    Use the gcode hook to start the camera grid documentation processes.
    """
    def hook_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if "M942" in cmd:
            self._logger.info( "Qeued command to start the Camera documentation" )

            # Get current Z Position
            if self._printer.get_current_data()["currentZ"]:
                self._currentZ = float(self._printer.get_current_data()["currentZ"])
            else:
                self._currentZ = 0.0

            # switch to pimary extruder, since the head camera is relative to this extruder and the offset to PNP nozzle might not be known (firmware offset)
            self._printer.commands("T0")
            self._printer.commands("G1 Z" + str(self._currentZ+5) + " F" + str(self.FEEDRATE)) # lift printhead

            for eachItem in self.CameraGridCoordsList[0]:
                # move camera to grid position
                self._logger.info( "Move camera to position X: %s Y: %s", str(eachItem.x), str(eachItem.y))
                cmd = "G1 X" + str(eachItem.x) + " Y" + str(eachItem.y) + " F" + str(self.FEEDRATE)
                self._printer.commands(cmd)

            self._printer.commands("G1 Z" + str(self._currentZ-5) + " F" + str(self.FEEDRATE)) # lower printhead
            return "G4 P1" # return dummy command

    	if "M945" in cmd:
    	    self.get_camera_image(100, 80, self.get_camera_image_callback, False)


    def get_camera_image_callback(self, path):
    	print "returned image path: "
    	print path
        self.cameraImagePath = path

    def _openGCodeFiles(self, inputName):
        gcode = open( inputName, 'r' )
        readData = gcode.readlines()
        gcode.close()
        return readData

    def _moveCameraToCamGrid(self ,Xpos ,Ypos):
        # switch to pimary extruder, since the head camera is relative to this extruder and the offset to PNP nozzle might not be known (firmware offset)
        self._printer.commands("T0")
        # move camera to part position
        cmd = "G1 X" + str(Xpos) + " Y" + str(Ypos) + " F" + str(self.FEEDRATE)
        self._logger.info("Move camera to: " + cmd)
        self._printer.commands("G1 Z" + str(self._currentZ+5) + " F" + str(self.FEEDRATE)) # lift printhead
        self._printer.commands(cmd)
        self._printer.commands("G1 Z" + str(camera_offset[2]) + " F" + str(self.FEEDRATE)) # lower printhead

    """This function sets up the necessary values for the camera lookup grid steps,
    it tries to get legit values first and elsely uses hardcoded default values"""
    def _getAndSetGridResolution(self):
        # use the helper to retrieve the Pixel per Millimeter ratio
        PixelPerMillimeter = self.get_camera_resolution("HEAD")
        # TODO: Remove hardcoded position and just get a random picture
        # Use the Camera helper from OctoPNP to grab an actual Image from the HEAD camera
        self.get_camera_image(0, 0, self.get_camera_image_callback, True)
        # Perform actions when there was a proper picture found
        if(self.cameraImagePath):
            self._logger.info("The found image path was: ",self.cameraImagePath)
            imagePath = self.get_camera_image_callback
            width, height = self._get_image_size(imagePath)
            # Divide the resolution by the PixelPerMillimeter ratio
            self.CamPixelX = width / PixelPerMillimeter
            self.CamPixelY = height / PixelPerMillimeter
        # If no data could be retrieved use default values
        else:
            self._logger.info("No proper image found, using default values")
            self.CamPixelX = 15
            self.CamPixelY = 15


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
