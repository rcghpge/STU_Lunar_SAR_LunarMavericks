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
import API.EntityBehaviorFuncs as EB #TODO
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
        st.logger_fatal("Can't complete MoveToCoord because it has already been deleted from active commands.")
        # en_behavior.FailCommand(command_type, payload)


mover.OnMoveComplete(On_MoveComplete)

# TODO RotateToAzimuth command


# CAMERA COMMANDS

def CameraPan_Received(command: Command):
    payload: st.ParamMap = command.payload
    az = payload.GetParam(st.VarType.double, "Azimuth")
    el = payload.GetParam(st.VarType.double, "Elevation")
    en_behavior.CameraPan(az, el)
    en_behavior.CompleteCommand("CameraPan", st.ParamMap())

en_behavior.OnCommandReceived("CameraPan", CameraPan_Received)


def On_CameraCapDone(captureID: int, pixels: np.ndarray[np.uint8]):
    first_pixel = pixels[0, 0]
    st.OnScreenLogMessage("Camera capture done; first pixel value: " + str(first_pixel), "LTV Behavior", st.Severity.Info)

def CaptureImage_Received(command: Command):
    payload: st.ParamMap = command.payload
    exposure = payload.GetParam(st.VarType.double, "Exposure")
    en_behavior.OnCameraCaptureDone(exposure)
    en_behavior.CameraCapture(exposure)

#######################
##  Simulation Loop  ##
#######################

# Keep the sim running (if this loop exits early for any reason, the sim will end)
exit_flag = False
while not exit_flag:
    # No hot loop allowed
    LoopFreqHz = st.GetThisSystem().GetParam(st.VarType.double, "LoopFreqHz")
    time.sleep(1.0 / LoopFreqHz)

st.leave_sim()
