# wy_facifyUI.py
# Author: Wayne Yip
# Date: May 27, 2019

import maya.cmds as cmds
from functools import partial
import wy_kinematify
reload (wy_kinematify)

def kinematifyUI():
    
    # Create window
    if cmds.window('kinematifyWin', exists=1):
        cmds.deleteUI('kinematifyWin')
    window = cmds.window('kinematifyWin', title='Kinematify', sizeable=1)
    
    # Create form + UI elements
    form = cmds.formLayout(numberOfDivisions=100)

    startJointText = cmds.textFieldGrp(label='Start Joint ', adj=2, editable=0)
    startJointBtn = cmds.button(label='Set Selected',
        command=partial(checkSelectedJoint,
            startJointText
        )
    )
    endJointText = cmds.textFieldGrp(label='End Joint ', adj=2, editable=0)
    endJointBtn = cmds.button(label='Set Selected',
        command=partial(checkSelectedJoint,
            endJointText
        )
    )
    ikControlText = cmds.textFieldGrp(label='IK Control ', adj=2, editable=0)
    ikControlBtn = cmds.button(label='Set Selected',
        command=partial(checkSelectedControl,
            ikControlText
        )
    )
    ikfkSwitchControlText = cmds.textFieldGrp(label='IK/FK Switch Control ', adj=2, editable=0)
    ikfkSwitchControlBtn = cmds.button(label='Set Selected',
        command=partial(checkSelectedControl,
            ikfkSwitchControlText
        )
    )
    jointNameSuffixText = cmds.textFieldGrp(label='Joint Name Suffix ', adj=2)
    
    kinematifyBtn = cmds.button(label='Kinematify!', 
        command=partial(executeKinematify, 
            startJointText, endJointText, 
            ikControlText, ikfkSwitchControlText,
            jointNameSuffixText
        )
    )
    applyBtn = cmds.button(label='Apply', 
        command=partial(applyKinematify, 
            startJointText, endJointText, 
            ikControlText, ikfkSwitchControlText,
            jointNameSuffixText
        )
    )
    closeBtn = cmds.button(label='Close', 
        command="cmds.deleteUI('kinematifyWin')"
    )

    # Format UI elements
    cmds.formLayout(form, edit=1,
        attachForm=[
            (startJointText, 'top', 15),
            (startJointText, 'left', 0),
            (startJointBtn, 'top', 15),
            (startJointBtn, 'right', 10),

            (endJointText, 'left', 0),
            (endJointText, 'right', 0),
            (endJointBtn, 'right', 10),

            (ikControlText, 'left', 0),
            (ikControlText, 'right', 0),
            (ikControlBtn, 'right', 10),

            (ikfkSwitchControlText, 'left', 0),
            (ikfkSwitchControlText, 'right', 0),
            (ikfkSwitchControlBtn, 'right', 10),

            (jointNameSuffixText, 'left', 0),
            (jointNameSuffixText, 'right', 0),

            (kinematifyBtn, 'left', 5),
            (kinematifyBtn, 'bottom', 5),
            (applyBtn, 'bottom', 5),
            (closeBtn, 'bottom', 5),
            (closeBtn, 'right', 5)
        ],
            attachControl=[
            (startJointText, 'bottom', 5, endJointText),
            (startJointText, 'right', 5, startJointBtn),
            (startJointBtn, 'bottom', 5, endJointBtn),

            (endJointText, 'bottom', 5, ikControlText),
            (endJointText, 'right', 5, endJointBtn),
            (endJointBtn, 'bottom', 5, ikControlBtn),
            
            (ikControlText, 'bottom', 5, ikfkSwitchControlText),
            (ikControlText, 'right', 5, ikControlBtn),
            (ikControlBtn, 'bottom', 5, ikfkSwitchControlBtn),
            
            (ikfkSwitchControlText, 'bottom', 5, jointNameSuffixText),
            (ikfkSwitchControlText, 'right', 5, ikfkSwitchControlBtn),
            (ikfkSwitchControlBtn, 'bottom', 5, jointNameSuffixText),

            (jointNameSuffixText, 'bottom', 25, kinematifyBtn),

            (kinematifyBtn, 'right', 5, applyBtn),
            (closeBtn, 'left', 5, applyBtn)
        ],
        attachPosition=[
            (kinematifyBtn, 'right', 0, 33),
            (applyBtn, 'left', 0, 34),
            (applyBtn, 'right', 0, 66),
        ]
    )

    cmds.showWindow(window)


def checkSelectedJoint(jointText, *args):

    ikControl = cmds.ls(selection=1)

    if len(ikControl) != 1:
        cmds.confirmDialog(title='Error', message='Please select a joint.')
        return False

    elif cmds.objectType(ikControl) != 'joint':
        cmds.confirmDialog(title='Error', message='Object selected is not a joint.')
    
    else:
        cmds.textFieldGrp(jointText, edit=1, text=cmds.ls(selection=1)[0])


def checkSelectedControl(controlText, *args):

    control = cmds.ls(selection=1)

    if len(control) != 1:
        cmds.confirmDialog(title='Error', message='Please select a control curve.')
        return False

    elif cmds.objectType(control) != 'transform':
        cmds.confirmDialog(title='Error', message='Object selected is not a control curve.')
    
    else:
        cmds.textFieldGrp(controlText, edit=1, text=cmds.ls(selection=1)[0])
    

def executeKinematify(startJointText, endJointText, ikControlText, ikfkSwitchControlText, jointNameSuffixText, *args):

    applyKinematify(startJointText, endJointText, ikControlText, ikfkSwitchControlText, jointNameSuffixText)
    cmds.deleteUI('kinematifyWin')


def applyKinematify(startJointText, endJointText, ikControlText, ikfkSwitchControlText, jointNameSuffixText, *args):

    startJoint = cmds.textFieldGrp(startJointText, q=1, text=1)
    endJoint = cmds.textFieldGrp(endJointText, q=1, text=1)
    ikControl = cmds.textFieldGrp(ikControlText, q=1, text=1)
    ikfkSwitchControl = cmds.textFieldGrp(ikfkSwitchControlText, q=1, text=1)
    jointNameSuffix = cmds.textFieldGrp(jointNameSuffixText, q=1, text=1)

    if startJoint == '' or endJoint == '' or ikControl == '' or ikControl == '' or ikfkSwitchControl == '' or jointNameSuffix == '':
        cmds.confirmDialog(title='Error', message="Please fill in all text fields.")
        return

    if startJoint == endJoint:
        cmds.confirmDialog(title='Error', message="Start and end joints are identical.")
        return
    
    if ikControl == ikfkSwitchControl:
        cmds.confirmDialog(title='Error', message="IK control and IK/FK switch control are identical.")
        return
    
    wy_kinematify.kinematify(startJoint, endJoint, ikControl, ikfkSwitchControl, jointNameSuffix)