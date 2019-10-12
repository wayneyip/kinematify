# kinematify
![Kinematify_img1](https://raw.githubusercontent.com/wayneyip/kinematify/master/kinematify.gif)

Maya Python tool to automate IKFK blend setup on a given joint chain.

## Features
- Automatic creation of IK and FK joint chains
- Setup of "IK" attribute to control IK/FK blending from 0 to 1

## Instructions

- Place `wy_kinematify.py` and `wy_kinematifyUI.py` in your Maya Scripts folder, found in:
    - Windows: `C:\Users\<Your-Username>\Documents\maya\<20xx>\scripts`
    - OSX: `/Users/<Your-Username>/Library/Preferences/Autodesk/maya/<20xx>/scripts`
    - Linux: `/home/<Your-Username>/maya/<20xx>/scripts`
- Restart/open Maya, then open the Script Editor by:
	- Going to `Windows > General Editors > Script Editor`

		**or**
	- Left-clicking the `{;}` icon at the bottom-right of your Maya window
- Copy/paste and run the following code in your Script Editor:

	```
	import wy_kinematifyUI
	reload (wy_kinematifyUI)
	wy_kinematifyUI.kinematifyUI()
	```
	to launch the Kinematify tool UI.

- (Extra) Save the UI launch code to a shelf button:
	- Go to `File > Save Script to Shelf` in the Script Editor
	- Type in a name for the button (e.g. "Kinematify"), and hit OK
	- Kinematify should now be saved as a button in your shelf.

## Details

**Technologies**: Maya, Python

**Developer**: Wayne Yip

**Contact**: yipw@usc.edu

