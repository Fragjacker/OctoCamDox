'''
Created on 18.07.2017

@author: Dennis Struhs
'''

from GCode_processor import Coordinate
from copy import deepcopy

#===============================================================================
# Main class
#===============================================================================
class CameraGridMaker:

    def __init__(self,incomingCoordList,layer,CamResX,CamResY):
        # Stores the maximum Pixel size the camera provies.
        # Its in PixelxPixel Format
        self.CamPixelX = CamResX
        self.CamPixelY = CamResY

        # Stores the number of total tile rows
        self.rows = 0

        # Stores the incoming List of coordinates
        self.CordList = incomingCoordList[layer]

        # Stores the coordinates as tuples of x and y.
        # Implementation in class Coordinate
        self.workList = []

        # Stores the List of found centers for the Camera Run
        self.CameraCoords = []

        #Below values store the extreme values found during the processing process
        self.minX = None
        self.minY = None
        self.maxX = None
        self.maxY = None
        self.centerX = None
        self.centerY = None

        # Stores the mode of the tilemaker algorithm
        self.switcher = None

    #Creates the work list we're using for our computations
    #and sets up the Bounding Box values
    def getCoordinates(self):
        self.workList = []
        for eachEntry in self.CordList:
            Coord = Coordinate(
                eachEntry.x,
                eachEntry.y)
            self.findXYExtremas(Coord.x, Coord.y)
            self.computeCenterOfExtremes()
            self.workList.append(Coord)

    #Find the Extrema for the Bounding Box
    def findXYExtremas(self,NewX,NewY):
        #Initialize with some base values other than zero
        if (self.minX == None):
            self.minX = NewX
            self.maxX = NewX
            self.minY = NewY
            self.maxY = NewY
        else:
            if(NewX < self.minX):
                self.minX = NewX
            elif(NewX > self.maxX):
                self.maxX = NewX

            if(NewY < self.minY):
                self.minY = NewY
            elif(NewY > self.maxY):
                self.maxY = NewY

    #Compute the Center of the printed Object
    def computeCenterOfExtremes(self):
        self.centerX = (self.maxX+self.minX) / 2
        self.centerY = (self.maxY+self.minY) / 2

    #Makes a points symmetrical copy of the upper Camerasectorgrid
    def makePointSymmetry(self,inputList):
        symmetryList = []
        for eachItem in inputList:
            distX = self.centerX - eachItem.x
            distY = self.centerY - eachItem.y

            if(distY != 0):
                symmetryX = self.centerX + distX
                symmetryY = self.centerY + distY
                newCoord = Coordinate(symmetryX,symmetryY)
                symmetryList.insert(0, newCoord)

        #Update rows properly considering the point symmetry
        self.makeRowPointSymmetrical()
        return symmetryList

    #===========================================================================
    # Main Camera Grid computation Algortihm
    #===========================================================================
    # Refactored function
    def _setUpCoordinates(self, CameraCoords, newCoord, inputList, seeUp):
        for eachItem in CameraCoords:
            newCoord = Coordinate(eachItem.x, seeUp)
            inputList.append(newCoord)

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

        #Once the most right is reached
        #fill the Camcoords list from right to left
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
        self.switcher = 0
        while(True):
            self.switcher = 0
            #Rows that have the switcher module result
            #of 0 fill from left to right
            if(self.switcher % 2 == 0):
                reverserList = []
                seeUp = (currentYPos - self.CamPixelY)
                walkUp = (currentYPos - self.CamPixelY / 2)
                if(walkUp > self.minY):
                    if(seeUp > self.minY):
                        self._setUpCoordinates(
                            self.CameraCoords, newCoord, reverserList, seeUp)

                        reverserList.reverse()
                        reverserList.extend(cacheList)
                        cacheList = deepcopy(reverserList)
                        currentYPos = seeUp
                        self.switcher += 1
                        self.incrementRow()
                    elif(seeUp <= self.minY):
                        self._setUpCoordinates(
                            self.CameraCoords, newCoord, reverserList, seeUp)

                        reverserList.reverse()
                        reverserList.extend(cacheList)
                        cacheList = deepcopy(reverserList)
                        currentYPos = seeUp
                        self.switcher += 1
                        self.incrementRow()
                        break
                else:
                    break
            #Rows that have the switcher module result
            # of 1 fill from right to left
            if(self.switcher % 2 == 1):
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
                        self.switcher -= 1
                        self.incrementRow()
                    elif(seeUp <= self.minY):
                        self._setUpCoordinates(
                            self.CameraCoords, newCoord, localList, seeUp)

                        localList.extend(cacheList)
                        cacheList = deepcopy(localList)
                        currentYPos = seeUp
                        self.switcher -= 1
                        self.incrementRow()
                        break
                else:
                    break

        #Insert the new list items into the Cameracoordinate List
        cacheList.extend(self.CameraCoords)
        self.CameraCoords = cacheList

        #Create the lower half of the Grid
        #by making a point symmetrical Copy
        self.CameraCoords.extend(self.makePointSymmetry(cacheList))

    #===========================================================================
    # Grid optimizer algorithm
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
            locSwitch = self.switcher
            # Initilize index depending on last switcher mode
            if(self.switcher == 0):
                index = elemPerRow-1
            else:
                index = 0
            # Mark the tiles for deletion now but preserve the array index
            while(index < len(localList)):
                if(locSwitch == 1):
                    localList[index] = None # Assign None to keep index intact
                    index += (elemPerRow*2)-1
                    locSwitch -= 1
                elif(locSwitch == 0):
                    localList[index] = None # Assign None to keep index intact
                    index += 1
                    locSwitch += 1
            # Now remove the None items
            localList = [x for x in localList if x is not None]
            # Move the grid to the left
            gridCenterX, gridCenterY = self.getCenterOfGrid( localList )
            for eachItem in localList:
                eachItem.x = eachItem.x + gridCenterX
                eachItem.y = eachItem.y + gridCenterY
            # Once the grid was moved get new Extrema bounds
            if(self.switcher == 0):
                newMinX, newMaxX = self.getGridXExtrema( localList , "RightToLeft" , elemPerRow-1)
            elif(self.switcher == 1):
                newMinX, newMaxX = self.getGridXExtrema( localList , "LeftToRight" , elemPerRow-1)
            # Check if the Grid is still covering everything
            if( self.minX >= newMinX and self.maxX <= newMaxX ):
                self.CameraCoords = deepcopy(localList)

#------------------------------------------------------------------------------

    def getCenterOfGrid( self, inputlist ):
        coordCenterX = 0
        coordCenterY = 0
        for eachItem in inputlist:
            coordCenterX += eachItem.x
            coordCenterY += eachItem.y
        # Generate the average
        coordCenterX = coordCenterX / len( inputlist )
        coordCenterY = coordCenterY / len( inputlist )
        # Make the difference between the current Center
        coordCenterX = self.centerX - coordCenterX
        coordCenterY = self.centerY - coordCenterY
        return coordCenterX, coordCenterY

    def getGridYExtrema( self, inputlist ):
        locminY = inputlist[0].y - ( self.CamPixelY / 2 )
        locmaxY = inputlist[len( inputlist ) - 1].y + ( self.CamPixelY / 2 )
        return locminY, locmaxY

    def getGridXExtrema( self, inputlist , mode , edgeElement):
        if(mode == "RightToLeft"):
            locmaxX = inputlist[0].x + ( self.CamPixelX / 2 )
            locminX = inputlist[edgeElement].x - ( self.CamPixelX / 2 )
            return locminX, locmaxX
        if(mode == "LeftToRight"):
            locminX = inputlist[0].x - ( self.CamPixelX / 2 )
            locmaxX = inputlist[edgeElement].x + ( self.CamPixelX / 2 )
            return locminX, locmaxX

    def getElementsPerRow( self, inputList ):
        elemPerRow = len( inputList ) / self.getRows()
        return elemPerRow

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
            if(self.switcher is 0):
                newCoord = Coordinate(self.CameraCoords[index].x + self.getCampixelX(),self.CameraCoords[index].y - self.getCampixelY())
                newCoord.set_mode("walk")
                self.switcher += 1
            elif(self.switcher is 1):
                newCoord = Coordinate(self.CameraCoords[index].x - self.getCampixelX(),self.CameraCoords[index].y - self.getCampixelY())
                newCoord.set_mode("walk")
                self.switcher -= 1
            localList.insert(index+counter, newCoord)
            counter += 1
            index += step
        self.CameraCoords = deepcopy(localList)

#===========================================================================
# Get and Set functions
#===========================================================================

    def getRows(self):
        return self.rows

    def incrementRow(self):
        self.rows += 1

    def makeRowPointSymmetrical(self):
        self.rows = (self.rows * 2) - 1

    def getMinX(self):
        return self.minX

    def getMaxX(self):
        return self.maxX

    def getMinY(self):
        return self.minY

    def getMaxY(self):
        return self.maxY

    def getCampixelX(self):
        return self.CamPixelX

    def getCampixelY(self):
        return self.CamPixelY

    def getCenterX(self):
        return self.centerX

    def getCenterY(self):
        return self.centerY

    def getCameraCoords(self):
        return self.CameraCoords
