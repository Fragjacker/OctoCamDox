'''
Created on 13.10.2017
The purpose is to implement additional options for the Grid generation.

@author: Dennis Struhs
'''
import CameraCoordinateGetter as CCGet
from GCode_processor import Coordinate
from copy import deepcopy

"""Inherited from the CameraGridMaker Class 
found in the CameraCoordinateGetter.py file"""
class CameraGridMakerWithOptions(CCGet.CameraGridMaker, object):
    
    _settings = None
    
    def __init__(self,settings,incomingCoordList, layer, CamResX, CamResY):
        super(CameraGridMakerWithOptions,self).__init__(incomingCoordList, layer, CamResX, CamResY)
        self._settings = settings
        
    #===========================================================================
    # Override of the Main Camera Grid computation Algortihm
    #===========================================================================
    def createCameraLookUpGrid(self):
        self.CameraCoords = []
        
        currentXPos = self.centerX
        seeRight = currentXPos
        walkRight = currentXPos
        #Walk all the way right first until maxX bound is reached
        while(True):
            seeRight = (currentXPos + self.CamPixelX)
            walkRight = (currentXPos + self.CamPixelX / 2)
            if(walkRight < self.maxX):
                if(seeRight < self.maxX):
                    currentXPos += self.CamPixelX
                elif(seeRight >= self.maxX):
                    currentXPos += self.CamPixelX
                    break
            else:
                break

        #Once the most left is reached
        #fill the Camcoords list from left to right
        seeLeft = currentXPos
        walkLeft = currentXPos
        while(True):
            seeLeft = (currentXPos - self.CamPixelX)
            walkLeft = (currentXPos - self.CamPixelX / 2)
            if(walkLeft > self.minX):
                if(seeLeft > self.minX):
                    newCoord = Coordinate(currentXPos, self.centerY)
                    self.CameraCoords.append(newCoord)
                    currentXPos -= self.CamPixelX
                elif(seeLeft <= self.minX):
                    newCoord = Coordinate(currentXPos, self.centerY)
                    self.CameraCoords.append(newCoord)
                    currentXPos -= self.CamPixelX
                    newCoord = Coordinate(currentXPos, self.centerY)
                    self.CameraCoords.append(newCoord)
                    break
            else:
                newCoord = Coordinate(currentXPos, self.centerY)
                self.CameraCoords.append(newCoord)
                break
        self.incrementRow()


        #Now create the x-Axis lines
        cacheList = []
        currentYPos = self.centerY
        while(True):
            localList = []
            seeUp = (currentYPos - self.CamPixelY)
            walkUp = (currentYPos - self.CamPixelY / 2)
            if(walkUp > self.minY):
                if(seeUp > self.minY):
                    self._setUpCoordinates(
                        self.CameraCoords, newCoord, localList, seeUp)

                    localList.extend(cacheList)
                    cacheList = deepcopy(localList)
                    currentYPos = seeUp
                    self.incrementRow()
                elif(seeUp <= self.minY):
                    self._setUpCoordinates(
                        self.CameraCoords, newCoord, localList, seeUp)

                    localList.extend(cacheList)
                    cacheList = deepcopy(localList)
                    currentYPos = seeUp
                    self.incrementRow()
                    break
            else:
                break

        #Insert the new list items into the Cameracoordinate List
        cacheList.extend(self.CameraCoords)
        self.CameraCoords = deepcopy(cacheList)

        #Create the lower half of the Grid
        #by making a point symmetrical Copy
        self.CameraCoords.extend(self.makePointSymmetry(cacheList))
        
        if(self._settings["forceLTR"]):
            self.flipListVertical()

    """Flip the list vertical to achieve a pure Left to Right layout"""
    def flipListVertical(self):
        tempList = []
        index = 0
        listEnd = (len(self.CameraCoords)-1)
        while (index <= listEnd):
            flippedCoord = Coordinate(
                self.CameraCoords[listEnd-index].x,
                self.CameraCoords[index].y)
            tempList.append(flippedCoord)
            index += 1
        self.CameraCoords = deepcopy(tempList)
