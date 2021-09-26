#Author-Ian Rist
#Description-Creates a Chamfer using a Patch for Cleaner Edge Break Toolpaths

import adsk.core, adsk.fusion, adsk.cam, traceback
import math

_app: adsk.core.Application = None
_ui: adsk.core.UserInterface = None
_handlers = []

def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface

        # Create the command definition for the feature create.
        cleanChamferCreateCmdDef = _ui.commandDefinitions.addButtonDefinition('irCleanChamferCreate', 'Clean Chamfer', 'Creates a new body with a clean chamfer surface.', 'Resources/Button')

        # Add the create button the user interface.
        createPanel = _ui.allToolbarPanels.itemById('SolidModifyPanel')
        cntrl: adsk.core.CommandControl = createPanel.controls.addCommand(cleanChamferCreateCmdDef, 'FusionChamferCommand', False)
        cntrl.isPromoted = True
        cntrl.isPromotedByDefault = True

        # Connect the handler to the command created event for the clean create.
        onCommandCreated = CCCreateCommandCreatedHandler()
        cleanChamferCreateCmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)



    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    _ui = None
    try:
        _app = adsk.core.Application.get()
        _ui: adsk.core.UserInterface  = _app.userInterface
        createPanel = _ui.allToolbarPanels.itemById('SolidModifyPanel')
        cmdCntrl = createPanel.controls.itemById('irCleanChamferCreate')
        if cmdCntrl:
            cmdCntrl.deleteMe()

        cleanChamferCreateCmdDef = _ui.commandDefinitions.itemById('irCleanChamferCreate')
        if cleanChamferCreateCmdDef:
            cleanChamferCreateCmdDef.deleteMe()

    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the emboss creation command created event.
class CCCreateCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            des: adsk.fusion.Design = _app.activeProduct
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            # Add the inputs to the command dialog.
            pointSelInput = inputs.addSelectionInput('edges', 'Edge', 'Select the edge to Chamfer.')
            pointSelInput.addSelectionFilter('NonTangentEdges')
            pointSelInput.setSelectionLimits(1)
            pointSelInput.isFullWidth = True

            chainCmd = inputs.addBoolValueInput('chain', 'Chain Selection', True, "", True)
            chamferStyle = inputs.addDropDownCommandInput('style', 'Chamfer Type', adsk.core.DropDownStyles.TextListDropDownStyle)
            chamferStyle.isFullWidth = True
            chamferStyle.isVisible = False
            dropdownItems = chamferStyle.listItems
            dropdownItems.add('Equal Distance', True, '')
            dropdownItems.add('Distance and Angle', False, '')

            inputs.addValueInput('width', 'Chamfer Width', des.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByString("0.05 in"))

            angleCmd = inputs.addAngleValueCommandInput('angle', 'Chamfer Angle', adsk.core.ValueInput.createByString("45 Deg"))
            angleCmd.maximumValue = 0.5*math.pi
            angleCmd.isMaximumValueInclusive = False
            angleCmd.isMinimumValueInclusive = False
            angleCmd.isVisible = False

            previewCmd = inputs.addBoolValueInput('preview', 'Preview Selection', True, "", True)


            onPreSelect = PreSelectHandler()
            cmd.preSelect.add(onPreSelect)
            _handlers.append(onPreSelect)

            onInputChanged = CreateInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)

            onExecutePreview = CreateExecutePreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            _handlers.append(onExecutePreview)

            onExecute = CreateExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)

            onPreSelectEnd = MyPreSelectEndHandler()
            cmd.preSelectEnd.add(onPreSelectEnd)
            _handlers.append(onPreSelectEnd)

            onSelect = MySelectHandler()
            cmd.select.add(onSelect)
            _handlers.append(onSelect) 
            
            onUnSelect = MyUnSelectHandler()
            cmd.unselect.add(onUnSelect)            
            _handlers.append(onUnSelect) 

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class PreSelectHandler(adsk.core.SelectionEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.SelectionEventArgs):
        try:
            eventArgs = adsk.core.SelectionEventArgs.cast(args)
            selectedEdge = adsk.fusion.BRepEdge.cast(eventArgs.selection.entity)
            if selectedEdge and eventArgs.firingEvent.sender.commandInputs.itemById("chain").value:
                args.additionalEntities = selectedEdge.tangentiallyConnectedEdges
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MyPreSelectEndHandler(adsk.core.SelectionEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.SelectionEventArgs):
        try:
            design = adsk.fusion.Design.cast(_app.activeProduct)
            selectedEdge = adsk.fusion.BRepEdge.cast(args.selection.entity) 
            if design and selectedEdge:
                for group in design.rootComponent.customGraphicsGroups:
                    if group.id == str(selectedEdge.tempId):
                        group.deleteMe()
                        break       
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
                
class MySelectHandler(adsk.core.SelectionEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.SelectionEventArgs):
        try:
            selectedEdge = adsk.fusion.BRepEdge.cast(args.selection.entity) 
            if selectedEdge and args.activeInput:
                args.activeInput.addSelection(selectedEdge)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
                
class MyUnSelectHandler(adsk.core.SelectionEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.SelectionEventArgs):
        try:
            selectedEdge = adsk.fusion.BRepEdge.cast(args.selection.entity)
            if selectedEdge and args.activeInput:
                curEdges = GetEdgeCollection(args.activeInput)
                args.activeInput.clearSelection()
                curEdges.removeByIndex(selectedEdge)
                args.activeInput.addSelection(curEdges)
            
            _ui.messageBox(str(args.selection.entity.objectType))

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CreateInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input
            

            if cmdInput.id == "style":
                angle: adsk.core.AngleValueCommandInput = inputs.itemById('angle')
                styleObj: adsk.core.DropDownCommandInput = inputs.itemById('style')
                style = styleObj.selectedItem.name
                if style == "Equal Distance":
                    angle.isVisible = False

                elif style == "Distance and Angle":
                    selections: adsk.core.SelectionCommandInput = inputs.itemById("edges")
                    isSel = selections.selectionCount
                    if False:#isSel > 0:
                        pointone: adsk.core.Point3D = selections.selection(0).point
                        pointtwo: adsk.core.Point3D = selections.selection(0).point
                        pointthree: adsk.core.Point3D = selections.selection(isSel-1).point
                        a, b, c = pointone.x-pointtwo.x, pointone.y-pointtwo.y, pointone.z-pointtwo.z
                        d, e, f = pointone.x-pointthree.x, pointone.y-pointthree.y, pointone.z-pointthree.z
                        vOne: adsk.core.Vector3D = adsk.core.Vector3D.create(a,b,c)
                        vTwo: adsk.core.Vector3D = adsk.core.Vector3D.create(d,e,f)
                        vOne.normalize()
                        vTwo.normalize()
                        vThree: adsk.core.Vector3D = vOne.crossProduct(vTwo)
                        vFour: adsk.core.Vector3D = vOne.crossProduct(vThree)
                        vThree.normalize()
                        vFour.normalize()
                        _ui.messageBox(str(vOne.asArray()))
                        _ui.messageBox(str(vTwo.asArray()))
                        _ui.messageBox(str(vThree.asArray()))
                        _ui.messageBox(str(vFour.asArray()))
                        angle.setManipulator(pointone, vThree, vFour)
                    else:
                        pass
                    angle.isVisible = True

                else:
                    angle.isVisible = True
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



class CreateExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            # Get the inputs.
            edgeSel: adsk.core.SelectionCommandInput = inputs.itemById('edges')
            widthInput: adsk.core.ValueCommandInput = inputs.itemById('width')
            angleInput: adsk.core.AngleValueCommandInput = inputs.itemById('angle')
            typeInput: adsk.core.DropDownCommandInput = inputs.itemById('style')
            chainInput: adsk.core.BoolValueCommandInput = inputs.itemById("chain")
            previewInput: adsk.core.BoolValueCommandInput = inputs.itemById('preview')

            # Show the lines if they are not currently selecting them
            design = adsk.fusion.Design.cast(_app.activeProduct)
            if design and previewInput.value == True:
                cggroup = design.rootComponent.customGraphicsGroups.add()
                for i in range(0, edgeSel.selectionCount):
                    edge = adsk.fusion.BRepEdge.cast(edgeSel.selection(i).entity)
                    cgcurve = cggroup.addCurve(edge.geometry)
                    cgcurve.color = adsk.fusion.CustomGraphicsSolidColorEffect.create(adsk.core.Color.create(0,127,255,255))
                    cgcurve.weight = 2
                    cgcurve.isSelectable = True

            # Preview if they have preview turned on and they are not currently selecting
            if previewInput.value == True:
                # Create the Chamfer.
                CreateChamfer(edgeSel, widthInput.value, angleInput.value, typeInput.selectedItem.name, chainInput.value)

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class CreateExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            # Get the inputs.
            edgeSel: adsk.core.SelectionCommandInput = inputs.itemById('edges')
            widthInput: adsk.core.ValueCommandInput = inputs.itemById('width')
            angleInput: adsk.core.AngleValueCommandInput = inputs.itemById('angle')
            typeInput: adsk.core.DropDownCommandInput = inputs.itemById('style')
            chainInput: adsk.core.BoolValueCommandInput = inputs.itemById("chain")

            # Create the Chamfer.
            CreateChamfer(edgeSel, widthInput.value, angleInput.value, typeInput.selectedItem.name, chainInput.value)

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Get the Edges out of the Selection Component
def GetEdgeCollection(edges: adsk.core.SelectionCommandInput):
    edgeCollection: adsk.core.ObjectCollection = adsk.core.ObjectCollection.create()
    for i in range(0, edges.selectionCount):
        edgeCollection.add(edges.selection(i).entity)
    return edgeCollection

def CreateChamfer(edges: adsk.core.SelectionCommandInput, widVal: float, angVal: float, typeVal: str, chain: bool):
    try:
        chamferSucess = True
        # Get the body the edges are part of.
        originalBody: adsk.fusion.BRepBody = edges.selection(0).entity.body

        # Get the Edges out of the Selection Component
        edgeCollection: adsk.core.ObjectCollection = GetEdgeCollection(edges)

        # Copy the body
        parentComponent: adsk.fusion.Component = originalBody.parentComponent

        # Create the Chamfer object.
        chamfers: adsk.fusion.ChamferFeatures = parentComponent.features.chamferFeatures
        try:
            # Create the input for the chamfer feature
            input = chamfers.createInput2()
            if typeVal == "Equal Distance":
                input.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edgeCollection, adsk.core.ValueInput.createByReal(widVal), chain)
            else:
                input.chamferEdgeSets.addDistanceAndAngleChamferEdgeSet(edgeCollection, adsk.core.ValueInput.createByReal(widVal), adsk.core.ValueInput.createByReal(angVal), False, chain)

            # Create the chamfer.
            chamfer = chamfers.add(input)

            # Select the faces of the Chamfer
            chamferFaces = chamfer.faces

            # Get the timeline Object of our first Feature
            firstTLN: adsk.fusion.TimelineObject =  chamfer.timelineObject

        except:
            chamferSucess = False

        if chamferSucess:
            chamferEdges: adsk.core.ObjectCollection = adsk.core.ObjectCollection.create()
            delFaces: adsk.core.ObjectCollection = adsk.core.ObjectCollection.create()
            for face in chamferFaces:
                for edge in face.edges:
                    chamferEdges.add(edge)
                delFaces.add(face)

            patchLoopEdges: adsk.core.ObjectCollection = adsk.core.ObjectCollection.create()
            for cEdge in chamferEdges:
                qFaces = cEdge.faces
                edgeLine = False

                for qFace in qFaces:
                    if not qFace in chamferFaces:
                        edgeLine = True
                if edgeLine:
                    patchLoopEdges.add(cEdge)

            firstLoopArr = []
            secondLoopArr = []
            useSecondLoop = False
            for edge in patchLoopEdges:
                if  edge in firstLoopArr or edge in secondLoopArr:
                    pass
                elif len(firstLoopArr) == 0:
                    firstLoopArr.append(edge)
                    tempprofile = edge.tangentiallyConnectedEdges
                    startIndex = tempprofile.find(edge)
                    profLen = tempprofile.count
                    for i in range(startIndex+1,profLen):
                        curEdge = tempprofile.item(i)
                        if curEdge in patchLoopEdges and not curEdge in firstLoopArr:
                            firstLoopArr.append(curEdge)
                    for i in range(0, startIndex-1):
                        curEdge = tempprofile.item(i)
                        if curEdge in patchLoopEdges and not curEdge in firstLoopArr:
                            firstLoopArr.append(curEdge)
                elif (firstLoopArr[0].endVertex == firstLoopArr[-1].startVertex or firstLoopArr[-1].endVertex == firstLoopArr[0].startVertex):
                    if len(secondLoopArr) == 0:
                        useSecondLoop = True
                        secondLoopArr.append(edge)
                    tempprofile = edge.tangentiallyConnectedEdges
                    startIndex = tempprofile.find(edge)
                    profLen = tempprofile.count
                    for i in range(startIndex+1,profLen):
                        curEdge = tempprofile.item(i)
                        if curEdge in patchLoopEdges and not curEdge in secondLoopArr:
                            secondLoopArr.append(curEdge)
                    for i in range(0, startIndex-1):
                        curEdge = tempprofile.item(i)
                        if curEdge in patchLoopEdges and not curEdge in secondLoopArr:
                            secondLoopArr.append(curEdge)  

            # Make the loops of contours of the area to be patched or lofted
            firstLoop: adsk.core.ObjectCollection = adsk.core.ObjectCollection.create()
            secondLoop: adsk.core.ObjectCollection = adsk.core.ObjectCollection.create()
            edgeArr = []
            for edge in firstLoopArr:
                firstLoop.add(edge)
            if useSecondLoop:
                for edge in secondLoopArr:
                    secondLoop.add(edge)
            else:
                for edgez in firstLoopArr:
                    edge: adsk.core.ObjectCollection = adsk.core.ObjectCollection.create()
                    edge.add(edgez)
                    bEdge: adsk.fusion.Path = parentComponent.features.createPath(edge)
                    edgeArr.append(bEdge)
                    

            firstLoopX: adsk.fusion.Path = parentComponent.features.createPath(firstLoop)
            if useSecondLoop:
                secondLoopX: adsk.fusion.Path = parentComponent.features.createPath(secondLoop)

            # Create collection of surfaces to be stitched at the end
            surfaces: adsk.core.ObjectCollection = adsk.core.ObjectCollection.create()

            # Check if there is two separate loops to make a loft out of
            if useSecondLoop:
                # Create loft feature input
                loftFeats: adsk.fusion.LoftFeatures = parentComponent.features.loftFeatures
                loftInput = loftFeats.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                loftSectionsObj = loftInput.loftSections
                loftSectionsObj.add(firstLoopX)
                loftSectionsObj.add(secondLoopX)
                loftInput.isSolid = False

                # Create loft feature
                myLoft: adsk.fusion.LoftFeature = loftFeats.add(loftInput)

                # Find the surface made by the loft
                surface = loftFeats.item(0).bodies.item(0)
                surfaces.add(surface)

            # Create a loft with a split path if there is only one path
            else:
                # Create loft feature input
                loftFeats: adsk.fusion.LoftFeatures = parentComponent.features.loftFeatures
                loftInput = loftFeats.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                loftSectionsObj = loftInput.loftSections
                for edge in edgeArr:
                    loftSectionsObj.add(edge)
                loftInput.isSolid = False

                # Create loft feature
                myLoft: adsk.fusion.LoftFeature = loftFeats.add(loftInput)

                # Find the surface made by the loft
                surface = loftFeats.item(0).bodies.item(0)
                surfaces.add(surface)

            # Delete the chamfer faces
            deletedFaces: adsk.fusion.SurfaceDeleteFaceFeatures = parentComponent.features.surfaceDeleteFaceFeatures
            surfs = deletedFaces.add(delFaces)

            # Get the bodies for the original body
            mainbods = originalBody
            bodyParts = surfs.bodies
            surfaces.add(mainbods)

            for face in bodyParts:
                surfaces.add(face)

            # Create a stitch input to be able to define the input needed for an stitch.
            stitches: adsk.fusion.StitchFeatures = parentComponent.features.stitchFeatures

            # Define tolerance with 1 cm.
            tolerance = adsk.core.ValueInput.createByReal(1.0)

            stitchInput = stitches.createInput(surfaces, tolerance, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

            # Create a stitch feature.
            stitch = stitches.add(stitchInput)

            # Get the final timeline object
            secondTLN: adsk.fusion.TimelineObject = stitch.timelineObject


            # Put all the features in a timeline group
            des = _app.activeProduct
            tgs: adsk.fusion.TimelineGroups = des.timeline.timelineGroups
            tg = tgs.add(firstTLN.index,secondTLN.index)
        else:
            pass

    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))