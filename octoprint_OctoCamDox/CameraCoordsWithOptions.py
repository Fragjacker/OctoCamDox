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

        if(self._settings.get(["forceLTR"])):
            self.flipListVertical()

    #===========================================================================
    # Override of the Grid optimizer algorithm
    #===========================================================================

    """The idea behind this algorithm is to remove the bottom row
    and then move the entire grid down to see if that brought
    an improvement over the previous grid."""
    def optimizeGrid( self ):
        # Save the original Cameracoords in case the optimization failed
        localList = deepcopy(self.CameraCoords)
        # Get elements per Row
        elemPerRow = self.getElementsPerRow( localList )
        # If there's only one row check for X-Axis optimization
#------------------------------------------------------------------------------
        if( self.rows == 1 ):
            # Remove last element of the list
            del localList[len( localList ) - 1]
            # Move the grid to the left
            gridCenterX, gridCenterY = self.getCenterOfGrid( localList )
            for eachItem in localList:
                eachItem.x = eachItem.x + gridCenterX
                eachItem.y = eachItem.y + gridCenterY
            # Once the grid was moved get new Extrema bounds
            newMinX, newMaxX = self.getGridXExtrema( localList , "RightToLeft" , elemPerRow-2)
            # Check if the Grid is still covering everything
            if( self.minX >= newMinX and self.maxX <= newMaxX ):
                self.CameraCoords = deepcopy(localList)

        # If row is greater than 1 we do more sophisticated optimizations
#------------------------------------------------------------------------------
        if( self.rows > 1 ):
            # Remove last row
            del localList[elemPerRow * ( self.getRows() - 1 ):len( localList )]

            # Move the grid down into the center
            gridCenterX, gridCenterY = self.getCenterOfGrid( localList )
            for eachItem in localList:
                eachItem.x = eachItem.x + gridCenterX
                eachItem.y = eachItem.y + gridCenterY
            # Once the grid was moved get new Extrema bounds
            newMinY, newMaxY = self.getGridYExtrema( localList )
            # Check if the Grid is still covering everything
            if( self.minY >= newMinY and self.maxY <= newMaxY ):
                self.CameraCoords = deepcopy(localList)
                self.rows -= 1

            # Remove tiles on the X-Axis and then check if all is still covered
            localList = deepcopy( self.CameraCoords ) # Get a fresh copy of list
            # Initilize index based on mode
            if(self._settings.get(["forceRTL"])):
                index = 0
            elif(self._settings.get(["forceLTR"])):
                index = elemPerRow-1
            # Mark the tiles for deletion now but preserve the array index
            while(index < len(localList)):
                localList[index] = None # Assign None to keep index intact
                index += elemPerRow
            # Now remove the None items
            localList = [x for x in localList if x is not None]
            # Move the grid to the left
            gridCenterX, gridCenterY = self.getCenterOfGrid( localList )
            for eachItem in localList:
                eachItem.x = eachItem.x + gridCenterX
                eachItem.y = eachItem.y + gridCenterY
            # Once the grid was moved get new Extrema bounds
            if(self._settings.get(["forceRTL"])):
                newMinX, newMaxX = self.getGridXExtrema( localList , "RightToLeft" , elemPerRow)
            elif(self._settings.get(["forceLTR"])):
                newMinX, newMaxX = self.getGridXExtrema( localList , "LeftToRight" , elemPerRow)
            # Check if the Grid is still covering everything
            if( self.minX >= newMinX and self.maxX <= newMaxX ):
                self.CameraCoords = deepcopy(localList)

    #===========================================================================
    # Helper functions
    #===========================================================================

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

    """This will add additional coordinates to the camera coords list
    which will not be used for taking pictures but only move the head camera.
    this feature will help taking better pictures on printers with high
    backlash values."""
    def addSlipFlaps(self):
        step = self.getElementsPerRow(self.CameraCoords)
        index = 0
        counter = 0
        localList = deepcopy(self.CameraCoords)
        while (index < len(self.CameraCoords)):
            if(self._settings.get(["forceRTL"])):
                newCoord = Coordinate(self.CameraCoords[index].x + self.getCampixelX(),self.CameraCoords[index].y)
                newCoord.set_mode("walk")
            elif(self._settings.get(["forceLTR"])):
                newCoord = Coordinate(self.CameraCoords[index].x - self.getCampixelX(),self.CameraCoords[index].y)
                newCoord.set_mode("walk")
            localList.insert(index+counter, newCoord)
            counter += 1
            index += step
        self.CameraCoords = deepcopy(localList)
