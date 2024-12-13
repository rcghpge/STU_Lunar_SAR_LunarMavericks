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

from API.STU_Common import Command, _commandID_Str, CoordToXY
import API.EntityBehaviorFuncs as EB
import API.EntityTelemetry as ET
import API.SurfaceMovement as SM

en: st.Entity = st.GetThisSystem().GetParam(st.VarType.entityRef, "Entity")
planet: st.Entity = st.GetThisSystem().GetParam(st.VarType.entityRef, "Planet")
mover = SM.SurfaceMover(en, planet)
en_behavior = EB.EntityBehavior(en)

moving_back_to_comm_range = False

##############################
##  Move behaviors for LTV  ##
##############################


def MoveToCoord_Received(command: Command):
    payload: st.ParamMap = command.payload
    loc = payload.GetParam(st.VarType.doubleV3, "Loc")
    coord = st.PlanetUtils.Coord(loc, np.identity(3), mover.radius)
    mover.TurnAndMoveToCoord(coord)
    st.OnScreenLogMessage(f"{en.getName()} Behavior: Received MoveToCoord command; moving to XY {CoordToXY(coord)}.", 
                          "LTV Behavior", st.Severity.Info)
en_behavior.OnCommandReceived("MoveToCoord", MoveToCoord_Received)

def On_MoveComplete(payload : st.ParamMap):
    global moving_back_to_comm_range
    move_command_type = "MoveToCoord"
    move_command_id = _commandID_Str(en, move_command_type)

    # Handle special case for finishing moving back into comm range.
    # Fails all active commands.
    if moving_back_to_comm_range:
        moving_back_to_comm_range = False
        st.OnScreenLogMessage(f"{en.getName()} Behavior: Reporting all active commands failed after moving back into comm range", "LTV Behavior", st.Severity.Warning)
        act_cmd_copy = en_behavior.ActiveCommands().copy()
        for act_cmd_type in act_cmd_copy:
            en_behavior.FailCommand(act_cmd_type, payload)
        return

    if (move_command_type in en_behavior.ActiveCommands()):
        if en.HasParam("HasComms"):
            if en.GetParam(st.VarType.bool, "HasComms"):
                en_behavior.CompleteCommand(move_command_type, payload)
            else:
                st.OnScreenLogMessage(f"{en.getName()} Behavior: MoveToCoord can't be reported completed because of comms loss.", 
                                      "LTV Behavior", st.Severity.Info)
                # en_behavior.FailCommand(command_type, payload)
        else:
            en_behavior.CompleteCommand(move_command_type, payload)
    else:
        # NOTE: this case is hit when using Stop command
        # st.OnScreenLogMessage(f"{en.getName()} Behavior: MoveToCoord failed because of missing command in active commands.", 
        #                       "LTV Behavior", st.Severity.Error)
        st.logger_warn("Can't complete MoveToCoord because it has already been deleted from active commands. This could be due to a Stop command.")
        # en_behavior.FailCommand(command_type, payload)
mover.OnMoveComplete(On_MoveComplete)

# STOPPING MOVEMENT

def Stop_Received(command: Command):
    payload: st.ParamMap = command.payload
    if ("MoveToCoord" in en_behavior.ActiveCommands()):
        en.SetParam(st.VarType.string, "State", "Loiter")
        move_fail_payload = st.ParamMap()
        move_fail_payload.AddParam(st.VarType.string, "Reason", "Stop command received")
        en_behavior.FailCommand("MoveToCoord", move_fail_payload)
    st.OnScreenLogMessage(f"{en.getName()} Behavior: Received Stop command; stopping movement.", 
                          "LTV Behavior", st.Severity.Info)
    en_behavior.CompleteCommand("Stop", payload)
en_behavior.OnCommandReceived("Stop", Stop_Received)

# ROTATING TO AZIMUTH

def RotateToAzimuth_Received(command: Command):
    payload: st.ParamMap = command.payload
    az = payload.GetParam(st.VarType.double, "Azimuth")
    mover.TurnToAzimuth(az)
    #NOTE: azimuth param in here is negative due to a flaw in the SurfaceMover code. The external API has been corrected to 
    st.OnScreenLogMessage(f"{en.getName()} Behavior: Received TurnToAzimuth command; rotating to azimuth = {-az} degrees.", 
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
    # st.OnScreenLogMessage(f"{en.getName()} Behavior: Camera capture done; first red pixel value: " + str(first_pixel), "LTV Behavior", st.Severity.Info)

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

# PickUpAntenna command handling
def PickUpAntenna_Received(command: Command):
    payload: st.ParamMap = command.payload
    param_list_name = payload.GetParam(st.VarType.string, "ParamListName")
    result_code = en_behavior.PickUpObject(param_list_name)
    payload2 = st.ParamMap()
    payload2.AddParam(st.VarType.int32, "ResultCode", result_code)
    if result_code == 0:
        en_behavior.CompleteCommand("PickUpAntenna", payload2)
    else:
        en_behavior.FailCommand("PickUpAntenna", payload2)
en_behavior.OnCommandReceived("PickUpAntenna", PickUpAntenna_Received)

def PlaceDownAntenna_Received(command: Command):
    result_code = en_behavior.PlaceDownObject()
    payload = st.ParamMap()
    payload.AddParam(st.VarType.int32, "ResultCode", result_code)
    if result_code == 0:
        en_behavior.CompleteCommand("PlaceDownAntenna", payload)
    else:
        en_behavior.FailCommand("PlaceDownAntenna", payload)
en_behavior.OnCommandReceived("PlaceDownAntenna", PlaceDownAntenna_Received)

#######################
##  Simulation Loop  ##
#######################

ranIntoSomething = False
DEFAULT_ENTITY_RADIUS_M = 0.3

last_comm_coord: st.PlanetUtils.Coord = mover.GetCurrentCoord()

itr = 0

# Keep the sim running (if this loop exits early for any reason, the sim will end)
exit_flag = False
while not exit_flag:
    itr += 1
    # Default behavior for losing comms is to go back to where we last had comms
    if en.GetParam(st.VarType.bool, "HasComms"):
        if itr % 100 == 0:
            last_comm_coord: st.PlanetUtils.Coord = mover.GetCurrentCoord()
    else:
        # Also ensure 50 ticks pass between last comm coord and comm loss reaction
        if(not moving_back_to_comm_range and itr % 100 == 50):
            st.OnScreenLogMessage(f"{en.getName()} Behavior: Comm line of sight occluded; moving back to last point with comm.", 
                            "LTV Behavior", st.Severity.Warning)
            moving_back_to_comm_range = True
            mover.TurnAndMoveToCoord(last_comm_coord)
            # will be cleaned up in On_MoveComplete

    rel_vecs, radii, had_comms = ET.GetLidarObstacles(en)
    # st.logger_info("Lidar info: " + str(np.asarray(rel_vecs)) + ", " + str(np.asarray(radii)) + ", " + str(had_comms))
    
    ######################
    # Obstacle hit detection; you must include this code in your loop!
    # Use "ObstaclesStopMovement": false on SimEntity in the sim config to disable stopping on obstacles
    ran_into_something_thistime = False
    for i in range(len(rel_vecs)):
        rel_vec = rel_vecs[i]
        obstacle_radius = radii[i]
        distance_away = np.linalg.norm(rel_vec)
        separation = distance_away - DEFAULT_ENTITY_RADIUS_M - obstacle_radius
        if separation < 0.0:
            ran_into_something_thistime = True
            if not ranIntoSomething:
                st.OnScreenLogMessage(f"Entity {en.getName()} ran into an obstacle, {distance_away:.3f}m away with {obstacle_radius:.3f}m radius.", "LTV Behavior", st.Severity.Warning)
                # Handle stopping the entity
                if st.GetSimEntity().GetParam(st.VarType.bool, "ObstaclesStopMovement"):
                    if ("MoveToCoord" in en_behavior.ActiveCommands()):
                        en.SetParam(st.VarType.string, "State", "Loiter")
                        move_fail_payload = st.ParamMap()
                        move_fail_payload.AddParam(st.VarType.string, "Reason", "Hit Obstacle")
                        en_behavior.FailCommand("MoveToCoord", move_fail_payload)


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
