import maya.cmds as cmds
import re

def kinematify(mainChainStartJoint, mainChainEndJoint, ikControl, ikfkSwitch, jointNameSuffix):

	numLayers = getLayersBetweenJoints(startJoint, endJoint)

	# Create IK chain
	ikChain = cmds.duplicate(mainChainStartJoint, renameChildren=1)

	# ...Rename duplicated IK joints 
	for i, ikJoint in enumerate(ikChain):
		if cmds.objectType(ikJoint) == 'joint':
			ikJoint = cmds.rename(ikJoint, re.sub('{}.*'.format(jointNameSuffix), '_IK{}'.format(jointNameSuffix), ikJoint))
			ikChain.pop(i)
			ikChain.insert(i, ikJoint)

	# ...Remove extra duplicated joints at the end
	ikChainStartJoint = ikChain[0]
	ikChainEndJoint = getChildJointAtLayer(ikChainStartJoint, numLayers)
	ikChainEndJointChildren = cmds.listRelatives(ikChainEndJoint, children=1)
	if ikChainEndJointChildren is not None:
		cmds.delete(ikChainEndJointChildren)
	
	# ...Create IK handle
	ikHandle = cmds.ikHandle(startJoint=ikChainStartJoint, endEffector=ikChainEndJoint)[0]
	ikHandle = cmds.rename(ikHandle, ikControl.replace('_CTRL', '_IK'))
	cmds.parent(ikHandle, ikControl)

	# Create FK chain
	fkChain = cmds.duplicate(mainChainStartJoint, renameChildren=1)

	# ...Rename duplicated FK joints 
	for i, fkJoint in enumerate(fkChain):
		if cmds.objectType(fkJoint) == 'joint':
			fkJoint = cmds.rename(fkJoint, re.sub('{}.*'.format(jointNameSuffix), '_FK{}'.format(jointNameSuffix), fkJoint))
			fkChain.pop(i)
			fkChain.insert(i, fkJoint)

	# ...Remove extra duplicated joints at the end
	fkChainStartJoint = fkChain[0]
	fkChainEndJoint = getChildJointAtLayer(fkChainStartJoint, numLayers)
	fkChainEndJointChildren = cmds.listRelatives(fkChainEndJoint, children=1)
	if fkChainEndJointChildren is not None:
		cmds.delete(fkChainEndJointChildren)
		
	# Orient main chain to IK and FK chains
	orientAll(mainChainStartJoint, ikChainStartJoint, fkChainStartJoint)

	# Connect IKFK switch control to all orient constraints' attributes
	cmds.addAttr(ikfkSwitch, ln='IK', at='float', min=0, max=1, keyable=1)
	cmds.addAttr(ikfkSwitch, ln='FK', at='float', min=0, max=1, keyable=1)

	testNode = mainChainEndJoint
	for i in range(numLayers + 1):
		orientConstr = cmds.listConnections(testNode, type='orientConstraint')[0]
		attrs = cmds.listAttr(orientConstr, keyable=1)
		for attr in attrs:
			for fkJoint in fkChain:
				if fkJoint in attr:
					orientConstrAttr = orientConstr + '.' + attr
					ikfkSwitchFK = ikfkSwitch + '.FK'
					if not cmds.isConnected(ikfkSwitchFK, orientConstrAttr):
						cmds.connectAttr(ikfkSwitchFK, orientConstrAttr)
			for ikJoint in ikChain:
				if ikJoint in attr:
					orientConstrAttr = orientConstr + '.' + attr
					ikfkSwitchIK = ikfkSwitch + '.IK'
					if not cmds.isConnected(ikfkSwitchIK, orientConstrAttr):
						cmds.connectAttr(ikfkSwitchIK, orientConstrAttr)

		if i < numLayers:
			testNode = cmds.listRelatives(testNode, parent=1)[0]

	# Relate IK attribute to FK attribute		
	cmds.expression(string="%s = 1 - %s" % (ikfkSwitch + '.FK', ikfkSwitch + '.IK'))
	cmds.setAttr(ikfkSwitch + '.FK', keyable=0, channelBox=0)

	# Create FK controls
	fkControl = createFkControls(fkChainStartJoint, jointNameSuffix)

	# Parent constrain FK controls to the main chain's parent control
	mainChainParentJoint = getParentJoint(mainChainStartJoint)
	if mainChainParentJoint is not None:
		parentConstrs = cmds.listConnections(mainChainParentJoint, type='parentConstraint')
		if parentConstrs is not None:
			parentConstr = parentConstrs[0]
			parentCtrls = [ctrl for ctrl in cmds.listConnections(parentConstr, type='transform') if '_CTRL' in ctrl]
			if parentCtrls is not None:
				parentCtrl = parentCtrls[0]
				cmds.parentConstraint(parentCtrl, fkControl, maintainOffset=1)

	# Point constrain IK start to main chain start:
	cmds.pointConstraint(mainChainStartJoint, ikChainStartJoint)

	# Lock IK/FK switch attributes
	cmds.setAttr(ikfkSwitch+'.tx', keyable=0)
	cmds.setAttr(ikfkSwitch+'.ty', keyable=0)
	cmds.setAttr(ikfkSwitch+'.tz', keyable=0)
	cmds.setAttr(ikfkSwitch+'.rx', keyable=0)
	cmds.setAttr(ikfkSwitch+'.ry', keyable=0)
	cmds.setAttr(ikfkSwitch+'.rz', keyable=0)
	cmds.setAttr(ikfkSwitch+'.sx', keyable=0)
	cmds.setAttr(ikfkSwitch+'.sy', keyable=0)
	cmds.setAttr(ikfkSwitch+'.sz', keyable=0)
	cmds.setAttr(ikfkSwitch+'.visibility', keyable=0)

	# Handle controls/joints visibility
	cmds.connectAttr(ikfkSwitch + '.IK', ikControl+'.visibility')
	cmds.connectAttr(ikfkSwitch + '.FK', fkControl+'.visibility')
	cmds.setAttr(fkChainStartJoint+'.visibility', 0)
	cmds.setAttr(ikChainStartJoint+'.visibility', 0)

	# Group everything for cleanup 
	worldGroup = 'world'
	if not cmds.objExists(worldGroup):
		cmds.group(name=worldGroup, empty=1)

	ikfkGrp = cmds.group(
		ikChainStartJoint, fkChainStartJoint, fkControl, 
		name=mainChainStartJoint.replace(jointNameSuffix, '_IKFK_GRP')
	)
	cmds.parent(ikfkGrp, worldGroup)


def getLayersBetweenJoints(parentJoint, childJoint):
	
	numLayers = 0
	joint = childJoint
	while joint != parentJoint:
		joint = cmds.listRelatives(joint, parent=1)[0]
		numLayers += 1
	return numLayers
	

def getChildJointAtLayer(parentJoint, layer):
	
	joint = parentJoint

	while layer > 0:
		children = cmds.listRelatives(joint, children=1)
		joint = [child for child in children if cmds.objectType(child) == 'joint'][0]
		layer -= 1

	return joint
	

def orientAll(mainChainJoint, ikChainJoint, fkChainJoint):
	
	cmds.orientConstraint(ikChainJoint, fkChainJoint, mainChainJoint, maintainOffset=0)
	
	mainChildren = cmds.listRelatives(mainChainJoint, children=1)
	ikChildren = cmds.listRelatives(ikChainJoint, children=1)
	fkChildren = cmds.listRelatives(fkChainJoint, children=1)
	
	if mainChildren is not None and ikChildren is not None and fkChildren is not None:
		orientAll(mainChildren[0], ikChildren[0], fkChildren[0])


def getParentJoint(jnt):

	parents = cmds.listRelatives(jnt, parent=1)
	if parents is None:
		return None
	else:
		parent = parents[0]
		if cmds.objectType(parent) == 'joint':
			return parent
		else:
			return getParentJoint(parent)


def createFkControls(fkJoint, jointNameSuffix):

	fkChildren = cmds.listRelatives(fkJoint, children=1)
	if fkChildren is not None:
		numChildJoints = 0
		for fkChild in fkChildren:
			if cmds.objectType(fkChild) == 'joint':
				numChildJoints += 1
		if numChildJoints == 1: 
			fkControl = createControlSphere(1)
			fkControl = cmds.rename(fkControl, fkJoint.replace(jointNameSuffix, '_CTRL'))

			# Color handling
			if fkControl.startswith('LF'):
				cmds.color(fkControl, rgb=(0,0,1))
			elif fkControl.startswith('RT'):
				cmds.color(fkControl, rgb=(1,0,0))
			
			# Lock translation and scale
			cmds.setAttr(fkControl+'.tx', lock=1, keyable=0)
			cmds.setAttr(fkControl+'.ty', lock=1, keyable=0)
			cmds.setAttr(fkControl+'.tz', lock=1, keyable=0)
			cmds.setAttr(fkControl+'.sx', lock=1, keyable=0)
			cmds.setAttr(fkControl+'.sy', lock=1, keyable=0)
			cmds.setAttr(fkControl+'.sz', lock=1, keyable=0)

			# Create group node
			grp = cmds.group(fkControl, name=fkControl.replace('_CTRL', '_GRP'))
			cmds.matchTransform(grp, fkJoint)
			
			# Constrain joint to control
			cmds.parentConstraint(fkControl, fkJoint, maintainOffset=1)
			
			fkChildGrp = createFkControls(fkChildren[0], jointNameSuffix)
			if fkChildGrp is not None:
				cmds.parent(fkChildGrp, fkControl)

			return grp

	return None


def createControlSphere(radius):
	circleX = cmds.circle(r=radius, nr=[1,0,0])[0]
	circleY = cmds.circle(r=radius, nr=[0,1,0])[0]
	circleZ = cmds.circle(r=radius, nr=[0,0,1])[0]

	circleYShape = cmds.listRelatives(circleY, shapes=1)[0]
	circleZShape = cmds.listRelatives(circleZ, shapes=1)[0]

	cmds.parent(circleYShape, circleX, relative=1, shape=1)
	cmds.parent(circleZShape, circleX, relative=1, shape=1)

	cmds.delete(circleY)
	cmds.delete(circleZ)
	
	return circleX