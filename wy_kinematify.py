import maya.cmds as cmds

def kinematify(mainChainStartJoint, mainChainEndJoint, ikControl, ikfkSwitch, jointNameSuffix):

	mainChain = getJointChainBetween(mainChainStartJoint, mainChainEndJoint, [])
	numLayers = len(mainChain)

	# Create IK chain
	cmds.select(clear=1)
	ikChain = []
	for joint in mainChain:
		jointPos = cmds.xform(joint, q=1, rotatePivot=1, worldSpace=1)
		ikJoint = cmds.joint(
			position=jointPos,
			name=joint.replace(jointNameSuffix, '_IK'+jointNameSuffix),
			radius=cmds.joint(joint, q=1, radius=1)[0]
		)
		ikChain.append(ikJoint)

	ikChainStartJoint = ikChain[0]
	ikChainEndJoint = ikChain[len(ikChain)-1]

	# ...Create IK handle
	ikHandle = cmds.ikHandle(startJoint=ikChainStartJoint, endEffector=ikChainEndJoint)[0]
	ikHandle = cmds.rename(ikHandle, ikControl.replace('_CTRL', '_IK'))
	cmds.parent(ikHandle, ikControl)

	# Create FK chain
	cmds.select(clear=1)
	fkChain = []
	for joint in mainChain:
		jointPos = cmds.xform(joint, q=1, rotatePivot=1, worldSpace=1)
		fkJoint = cmds.joint(
			position=jointPos,
			name=joint.replace(jointNameSuffix, '_FK'+jointNameSuffix),
			radius=cmds.joint(joint, q=1, radius=1)[0]
		)
		fkChain.append(fkJoint)

	fkChainStartJoint = fkChain[0]
	fkChainEndJoint = fkChain[len(ikChain)-1]
		
	# Orient main chain to IK and FK chains
	orientConstrs = []
	for i in range(len(mainChain)):
		orientConstr = cmds.orientConstraint(ikChain[i], fkChain[i], mainChain[i], maintainOffset=1)[0]
		cmds.setAttr(orientConstr+'.interpType', 2) # Shortest interpolation
		orientConstrs.append(orientConstr)

	cmds.orientConstraint(ikControl, ikChainEndJoint, maintainOffset=1)

	# Connect IKFK switch control to all orient constraints' attributes
	cmds.addAttr(ikfkSwitch, ln='IK', at='float', min=0, max=1, keyable=1)
	cmds.addAttr(ikfkSwitch, ln='FK', at='float', min=0, max=1, keyable=1)

	for orientConstr in orientConstrs:
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

	# Point constrain IK start to main chain start
	cmds.pointConstraint(mainChainStartJoint, ikChainStartJoint)

	# Parent constraint IKFK switch to end joint
	cmds.parentConstraint(mainChainEndJoint, ikfkSwitch, maintainOffset=1)

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


def getJointChainBetween(startJoint, endJoint, jointChain):
	
	# Ensure that a joint chain exists between start and end joint
	startJointDescendants = cmds.listRelatives(startJoint, allDescendents=1)
	if startJointDescendants is None or endJoint not in startJointDescendants:
		cmds.error('No joint chain found between start and end joints')
		return
	
	joint = endJoint
	jointChain.append(joint)

	while joint != startJoint:
		joint = cmds.listRelatives(joint, parent=1)[0]
		jointChain.append(joint)

	jointChain.reverse()
	return jointChain
	

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

	fkControl = createControlSphere(0.5)
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

	fkChildren = cmds.listRelatives(fkJoint, children=1)
	if fkChildren is not None:

		numChildJoints = 0

		for fkChild in fkChildren:
			if cmds.objectType(fkChild) == 'joint':
				numChildJoints += 1

		if numChildJoints == 1: 
			fkChildGrp = createFkControls(fkChildren[0], jointNameSuffix)
			if fkChildGrp is not None:
				cmds.parent(fkChildGrp, fkControl)

	return grp


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