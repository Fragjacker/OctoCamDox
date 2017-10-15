'''
Created on 14.10.2017. Implements the stitching process
for the forced Right to Left and Left to Right option.

@author: Dennis Struhs
'''
import image_merger as imerge

"""Inherited from the ImageMerger class found
in the image_merger.py file"""
class ImageMergerWithOptions(imerge.ImageMerger, object):

    """Extend super class init method adding settings
    :param settings: Stores the _settings object reference"""
    def __init__(self,settings,ImageArray,tileRows):
        super(ImageMergerWithOptions,self).__init__(ImageArray,tileRows)
        self._settings = settings

    def mergeImages(self):
        # Update tile rows before we start stitching
        tileRows = self.tileRows
        tempImage1 = None
        tempImage2 = None
        self.MergedImage = None
        completedTwoRuns = False # Is true when there's two rows full
        # Stitch start from left to right
        if(self.checkForProperStitchCase() is "LeftToRight"):
            # Now stitch the other images
            i = 0
            rowcounter = 1
            numberOfRuns = 0
            colLength = len(self.ImageArray) / tileRows
            while(i < len(self.ImageArray)):
                if(colLength is rowcounter):
                    rowcounter = 1
                    i += 1
                    numberOfRuns += 1
                    if(numberOfRuns >= 2):
                        completedTwoRuns = True

                    # Stich the ready made rows vertically now
                    if(completedTwoRuns is True and self.MergedImage is None):
                        self.MergedImage = self.stitchImages(tempImage1,tempImage2,"vertical")
                        tempImage1 = None
                        tempImage2 = None
                    elif(completedTwoRuns is True and self.MergedImage is not None):
                        self.MergedImage = self.stitchImages(self.MergedImage,tempImage1,"vertical")
                        tempImage1 = None

                if(i < len(self.ImageArray)):
                    if(numberOfRuns >= 2):
                        if(tempImage1 is not None):
                            tempImage1 = self.stitchImages(tempImage1,self.ImageArray[i+1],"horizontal")
                        if(tempImage1 is None):
                            tempImage1 = self.stitchImages(self.ImageArray[i],self.ImageArray[i+1],"horizontal")
                    if(numberOfRuns < 2):
                        if(numberOfRuns == 0):
                            if(tempImage1 is not None):
                                tempImage1 = self.stitchImages(tempImage1,self.ImageArray[i+1],"horizontal")
                            if(tempImage1 is None):
                                tempImage1 = self.stitchImages(self.ImageArray[i],self.ImageArray[i+1],"horizontal")
                        if(numberOfRuns == 1):
                            if(tempImage2 is not None):
                                tempImage2 = self.stitchImages(tempImage2,self.ImageArray[i+1],"horizontal")
                            if(tempImage2 is None):
                                tempImage2 = self.stitchImages(self.ImageArray[i],self.ImageArray[i+1],"horizontal")

                    i += 1
                    rowcounter += 1

        # Stitch start from right to left
        if(self.checkForProperStitchCase() is "RightToLeft"):
            # Now stitch the other images
            i = 0
            rowcounter = 1
            numberOfRuns = 0
            colLength = len(self.ImageArray) / tileRows
            while(i < len(self.ImageArray)):
                if(colLength is rowcounter):
                    rowcounter = 1
                    i += 1
                    numberOfRuns += 1
                    if(numberOfRuns >= 2):
                        completedTwoRuns = True

                    # Stich the ready made rows vertically now
                    if(completedTwoRuns is True and self.MergedImage is None):
                        self.MergedImage = self.stitchImages(tempImage1,tempImage2,"vertical")
                        tempImage1 = None
                        tempImage2 = None
                    elif(completedTwoRuns is True and self.MergedImage is not None):
                        self.MergedImage = self.stitchImages(self.MergedImage,tempImage1,"vertical")
                        tempImage1 = None

                if(i < len(self.ImageArray)):
                    if(numberOfRuns >= 2):
                        if(tempImage1 is not None):
                            tempImage1 = self.stitchImages(self.ImageArray[i+1],tempImage1,"horizontal")
                        if(tempImage1 is None):
                            tempImage1 = self.stitchImages(self.ImageArray[i+1],self.ImageArray[i],"horizontal")
                    if(numberOfRuns < 2):
                        if(numberOfRuns == 0):
                            if(tempImage1 is not None):
                                tempImage1 = self.stitchImages(self.ImageArray[i+1],tempImage1,"horizontal")
                            if(tempImage1 is None):
                                tempImage1 = self.stitchImages(self.ImageArray[i+1],self.ImageArray[i],"horizontal")
                        if(numberOfRuns == 1):
                            if(tempImage2 is not None):
                                tempImage2 = self.stitchImages(self.ImageArray[i+1],tempImage2,"horizontal")
                            if(tempImage2 is None):
                                tempImage2 = self.stitchImages(self.ImageArray[i+1],self.ImageArray[i],"horizontal")

                    i += 1
                    rowcounter += 1

    """Decides the proper case for the Stitching process."""
    def checkForProperStitchCase(self):
        if(self._settings.get(["forceLTR"])):
            return "LeftToRight"
        if(self._settings.get(["forceRTL"])):
            return "RightToLeft"
