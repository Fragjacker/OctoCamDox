# OctoCamDox
OctoCamDox Plugin for Octoprint which allows for fully automated picture grabbing of printed layers using close-up camera shots to generate high resolution pictures by combining many pictures into one big one.

# Introduction
OctoCamDox is an extension that allows Octoprint to use printer head mounted industrial cameras to consecutively take images and then build a large high definition picture for each printed layer.
It currently requires the following hardware extensions::
* A head camera to take close-up images from the printed layers.

![OctoCamDox-Overview](https://user-images.githubusercontent.com/19975052/31948581-95886530-b8d7-11e7-80ec-65bee74951a3.JPG)

# Installation
## Prerequirements
To achieve higher compatibility and modularity, OctoCamDox doesn't access the cameras directly. Every time an image is required, OctoCamDox relies on a user defined helper function in order to call a script which must be adapted for every installation according to the deployed camera setup. OctoCamDox expects a set of correctly cropped and rotated images after executing the script. Filenames and path for images and script must be set in the settings dialog.

## Installing the package
The plugin itself can be installed as any regular python package:
`pip install https://github.com/platsch/OctoCamDox/archive/master.zip`

Make sure you use the same Python environment that you installed OctoPrint under, otherwise the plugin won't be able to satisfy its dependencies. Further information can be found in the Octoprint [documentation](http://docs.octoprint.org/en/devel/plugins/using.html)
OctoCamDox requires numpy and opencv2. Try installing those packages by hand if automatic dependency resolving fails.

## Data Format
The information for the Camera system is integrated into normal gcode files as a M942 command somewhere in the gcode. OctoCamDox extracts the required information automatically everytime a gcode file is loaded in Octoprint and will actively hook on the M942 command to start the image capturing process. Make sure the M942 command is inserted after a layer change when using your slicing software, such as slic3r.

# Configuration
Good configuration and calibration of the printer is absolutely crucial to successfully generate high definition close-up pictures using a head camera.
## Program constants
* Picture width: The width of the camera picture in pixels
* Picture height: The width of the camera picture in pixels
* Layer height: The height of the layer in Millimeter
* Target extruder: If you use multiple Extruder layouts enter the name of the Extruder that is used inside the gcode. If you use single-extruder setups, leave this blank.
## Camera Documentation Toggle
Toggle whether you want the printer to actively take images during the printig process or not, without having to deactivate the entire plug-in everytime
## Camera Grid Options
* Use normal mode: Generate the best and shortest path that the camera should take when capturing the pictures
* Force left to right: Force the grid generation to always walk from left to right when taking pictures. This is useful on printers with high backlash values in order to achieve seamless pictures.
* Force right to left: Force the grid generation to always walk from right to left when taking pictures. This is useful on printers with high backlash values in order to achieve seamless pictures.
* Add backlash flaps: Add additional "blind" coordinates that will not be considered for compiling the big picture but serve the purpose to circumvent backlash seams in the Y Axis on the resulting picture.

![OctoCamDox-Settings](https://user-images.githubusercontent.com/19975052/31948587-97673336-b8d7-11e7-99af-57b847c87f86.JPG)
