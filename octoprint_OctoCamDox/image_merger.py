'''
Created on 01.06.2017

@author: Dennis Struhs
'''

import cv2
import numpy as np

class ImageMerger():

    def __init__(self,ImageArray,tileRows):
        self.MergedImage = None
        self.ImageArray = ImageArray
        self.tileRows = tileRows

    def mergeImages(self):
        # Update tile rows before we start stitching
        tileRows = self.tileRows
        tempImage1 = None
        tempImage2 = None
        completedTwoRuns = False # Is true when there's two rows full
        i = 0
        rowcounter = 1
        numberOfRuns = 0
        colLength = len(self.ImageArray) / tileRows
        direction = "LeftToRight"
        while(i < len(self.ImageArray)):
            if(colLength is rowcounter):
                rowcounter = 1
                if(self.checkForProperStitchCase(tileRows) is "LeftToRight"):
                    if(direction is "LeftToRight"):
                        direction = "RightToLeft"
                    elif(direction is "RightToLeft"):
                        direction = "LeftToRight"
                if(self.checkForProperStitchCase(tileRows) is "RightToLeft"):
                    if(direction is "RightToLeft"):
                        direction = "LeftToRight"
                    elif(direction is "LeftToRight"):
                        direction = "RightToLeft"
                i += 1
                numberOfRuns += 1
                if(numberOfRuns >= 2):
                    completedTwoRuns = True
                # Stich the ready made rows vertically now
                if(completedTwoRuns is True and self.MergedImage is None):
                    if(direction is "RightToLeft"):
                        self.MergedImage = self.stitchImages(tempImage2,tempImage1,"vertical")
                        tempImage2 = None
                    if(direction is "LeftToRight"):
                        self.MergedImage = self.stitchImages(tempImage1,tempImage2,"vertical")
                        tempImage1 = None
                elif(completedTwoRuns is True and self.MergedImage is not None):
                    if(direction is "RightToLeft"):
                        self.MergedImage = self.stitchImages(self.MergedImage,tempImage1,"vertical")
                        tempImage2 = None
                    if(direction is "LeftToRight"):
                        self.MergedImage = self.stitchImages(self.MergedImage,tempImage2,"vertical")
                        tempImage1 = None

            if(i < len(self.ImageArray)):
                if(direction is "LeftToRight" and tempImage1 is not None):
                    tempImage1 = self.stitchImages(tempImage1,self.ImageArray[i+1],"horizontal")
                if(direction is "LeftToRight" and tempImage1 is None):
                    tempImage1 = self.stitchImages(self.ImageArray[i],self.ImageArray[i+1],"horizontal")
                if(direction is "RightToLeft" and tempImage2 is not None):
                    tempImage2 = self.stitchImages(self.ImageArray[i+1],tempImage2,"horizontal")
                if(direction is "RightToLeft" and tempImage2 is None):
                    tempImage2 = self.stitchImages(self.ImageArray[i+1],self.ImageArray[i],"horizontal")

                i += 1
                rowcounter += 1

    """Decides the proper case for the Stitching process."""
    def checkForProperStitchCase(self,tileRows):
        check1 = (tileRows / 2) % 2
        check2 = (tileRows / 3) % 3
        if(check1 or check2 is 1):
            return "LeftToRight"
        if(check1 or check2 is 0):
            return "RightToLeft"

    def stitchImages(self,IncomingImage1,IncomingImage2,mode):
        # Stitch images into rows
        if(mode is "horizontal"):
            return np.concatenate((IncomingImage1, IncomingImage2), axis=1)
        # Stitch top and bottom row image together
        if(mode is "vertical"):
            return np.concatenate((IncomingImage1, IncomingImage2), axis=0)

    def get_MergedImage(self):
        return self.MergedImage
