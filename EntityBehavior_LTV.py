# THIS COMMENT LINE SHOULD BE THE FIRST LINE OF THE FILE
# DON'T CHANGE ANY OF THE BELOW; NECESSARY FOR JOINING SIMULATION
import os, sys, time, datetime, traceback
import spaceteams as st
def custom_exception_handler(exctype, value, tb):
    error_message = "".join(traceback.format_exception(exctype, value, tb))
    st.logger_fatal(error_message)
    exit(1)
sys.excepthook = custom_exception_handler
st.connect_to_sim(sys.argv)
import numpy as np
# DON'T CHANGE ANY OF THE ABOVE; NECESSARY FOR JOINING SIMULATION
#################################################################

from API.STU_Common import Command, _commandID_Str
import API.EntityBehaviorFuncs as EB
import API.EntityTelemetry as ET
import API.SurfaceMovement as SM

en: st.Entity = st.GetThisSystem().GetParam(st.VarType.entityRef, "Entity")
planet: st.Entity = st.GetThisSystem().GetParam(st.VarType.entityRef, "Planet")
mover = SM.SurfaceMover(en, planet)
en_behavior = EB.EntityBehavior(en)

##############################
##  Move behaviors for LTV  ##
##############################


def MoveToCoord_Received(command: Command):
    payload: st.ParamMap = command.payload
    loc = payload.GetParam(st.VarType.doubleV3, "Loc")
    coord = st.PlanetUtils.Coord(loc, np.identity(3), mover.radius)
    mover.TurnAndMoveToCoord(coord)
    st.OnScreenLogMessage("Received MoveToCoord command; moving to specified coord.", 
                          "LTV Behavior", st.Severity.Info)


en_behavior.OnCommandReceived("MoveToCoord", MoveToCoord_Received)


def On_MoveComplete(payload : st.ParamMap):
    command_type = "MoveToCoord"
    command_id = _commandID_Str(en, command_type)
    # st.OnScreenLogMessage("Evaluating completion for command id: " + command_id, 
    #                       "LTV Behavior", st.Severity.Info)
    
    if (command_type in en_behavior.ActiveCommands()):
        if en.HasParam("HasComms"):
            if en.GetParam(st.VarType.bool, "HasComms"):
                en_behavior.CompleteCommand(command_type, payload)
            else:
                st.OnScreenLogMessage("MoveToCoord failed because of comms loss.", 
                                      "LTV Behavior", st.Severity.Info)
                en_behavior.FailCommand(command_type, payload)
        else:
            en_behavior.CompleteCommand(command_type, payload)
    else:
        st.OnScreenLogMessage("MoveToCoord failed because of missing command in active commands.", 
                              "LTV Behavior", st.Severity.Error)
        st.logger_warn("Can't complete MoveToCoord because it has already been deleted from active commands.")
        # en_behavior.FailCommand(command_type, payload)


mover.OnMoveComplete(On_MoveComplete)

def RotateToAzimuth_Received(command: Command):
    payload: st.ParamMap = command.payload
    az = payload.GetParam(st.VarType.double, "Azimuth")
    mover.TurnToAzimuth(az)
    st.OnScreenLogMessage("Received TurnToAzimuth command; rotating to a specified azimuth.", 
                        "LTV Behavior", st.Severity.Info)
    en_behavior.CompleteCommand("RotateToAzimuth", st.ParamMap())

en_behavior.OnCommandReceived("RotateToAzimuth", RotateToAzimuth_Received)

# CAMERA COMMANDS

def CameraPan_Received(command: Command):
    payload: st.ParamMap = command.payload
    az = payload.GetParam(st.VarType.double, "Azimuth")
    el = payload.GetParam(st.VarType.double, "Elevation")
    en_behavior.CameraPan(az, el)
    en_behavior.CompleteCommand("CameraPan", st.ParamMap())

en_behavior.OnCommandReceived("CameraPan", CameraPan_Received)

# Reaction to camera capture completing
def On_CameraCapDone( orig_command: Command,
                     captureID: int, 
                     capturedImage: st.CapturedImage):
    # first_pixel = capturedImage.PixelsR[0]
    # st.OnScreenLogMessage(f"Camera capture done; first red pixel value: " + str(first_pixel), "LTV Behavior", st.Severity.Info)

    payload = st.ParamMap()
    payload.AddParamArray(st.VarType.uint8, "PixelsR", capturedImage.PixelsR)
    payload.AddParamArray(st.VarType.uint8, "PixelsG", capturedImage.PixelsG)
    payload.AddParamArray(st.VarType.uint8, "PixelsB", capturedImage.PixelsB)
    payload.AddParam(st.VarType.int32, "ResolutionX", capturedImage.properties.ResolutionX)
    payload.AddParam(st.VarType.int32, "ResolutionY", capturedImage.properties.ResolutionY)
    payload.AddParam(st.VarType.double, "Exposure", capturedImage.properties.EV)
    payload.AddParam(st.VarType.double, "FOV", capturedImage.properties.FOV)
    en_behavior.CompleteCommand("CaptureImage", payload)

# CaptureImage command handling
def CaptureImage_Received(command: Command):
    payload: st.ParamMap = command.payload
    exposure = payload.GetParam(st.VarType.double, "Exposure")
    capture_id = en_behavior.CameraCapture(exposure)
    st.OnImageReceived(capture_id, lambda capturedImage: On_CameraCapDone(command, capture_id, capturedImage))

en_behavior.OnCommandReceived("CaptureImage", CaptureImage_Received)

#######################
##  Simulation Loop  ##
#######################

ranIntoSomething = False
DEFAULT_ENTITY_RADIUS_M = 0.3

last_comm_coord: st.PlanetUtils.Coord = mover.GetCurrentCoord()

# Keep the sim running (if this loop exits early for any reason, the sim will end)
exit_flag = False
while not exit_flag:
    # Default behavior for losing comms is to go back to where we last had comms
    if en.GetParam(st.VarType.bool, "HasComms"):
        last_comm_coord: st.PlanetUtils.Coord = mover.GetCurrentCoord()
    else:
        mover.TurnAndMoveToCoord(last_comm_coord)
        st.OnScreenLogMessage(f"Entity {en.getName()} comm line of sight occluded; Moving back to last point with comm", 
                            "LTV Behavior", st.Severity.Info)

    rel_vecs, radii, had_comms = ET.GetLidarObstacles(en)
    # st.logger_info("Lidar info: " + str(np.asarray(rel_vecs)) + ", " + str(np.asarray(radii)) + ", " + str(had_comms))
    
    ######################
    # WIP obstacle hit detection - TBD exact behavior
    ran_into_something_thistime = False
    for i in range(len(rel_vecs)):
        rel_vec = rel_vecs[i]
        obstacle_radius = radii[i]
        distance_away = np.linalg.norm(rel_vec)
        separation = distance_away - DEFAULT_ENTITY_RADIUS_M - obstacle_radius
        if separation < 0.0:
            ran_into_something_thistime = True
            if not ranIntoSomething:
                st.OnScreenLogMessage(f"Entity {en.getName()} ran into an obstacle, {distance_away}m away with {obstacle_radius}m radius.", "LTV Behavior", st.Severity.Warning)
                ranIntoSomething = True
    if not ran_into_something_thistime:
        if ranIntoSomething:
            st.OnScreenLogMessage(f"Entity {en.getName()} is no longer running into an obstacle.", "LTV Behavior", st.Severity.Warning)
        ranIntoSomething = False
    #######################

    # Loop delay so we don't use too much CPU resources
    LoopFreqHz = st.GetThisSystem().GetParam(st.VarType.double, "LoopFreqHz")
    time.sleep(1.0 / LoopFreqHz)

st.leave_sim()
