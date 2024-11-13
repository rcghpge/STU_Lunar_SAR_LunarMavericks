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

from API.STU_Common import *
import API.MissionManagerFuncs as MM
mm = MM.MissionManager()
import API.EntityTelemetry as ET
# ^ NECESSARY STU IMPORTS

import TaskGraph as TG
import cv2 # for camera pixel work

#############################
##  Mission Manager Setup  ##
#############################

# Get all entities participating in the search
entities = st.GetThisSystem().GetParamArray(st.VarType.entityRef, "Entities")
LTV1: st.Entity = entities[0]
LTV2: st.Entity = entities[1]
Scout1: st.Entity = entities[2]
Scout2: st.Entity = entities[3]

LTV1_task_graph = TG.TaskGraph()
LTV2_task_graph = TG.TaskGraph()
Scout1_task_graph = TG.TaskGraph()
Scout2_task_graph = TG.TaskGraph()


# Camera image processing
img_rgb = None
image_changed = False

def ProcessImage(image : st.CapturedImage):
    global img_rgb
    global image_changed
    resx = image.properties.ResolutionX
    resy = image.properties.ResolutionY
    img_r = np.array(image.PixelsR, dtype=np.uint8).reshape((resy, resx))
    img_g = np.array(image.PixelsG, dtype=np.uint8).reshape((resy, resx))
    img_b = np.array(image.PixelsB, dtype=np.uint8).reshape((resy, resx))

    # Stack channels into a single 3D array (height x width x 3)
    img_rgb = np.stack((img_b, img_g, img_r), axis=-1)
    image_changed = True

###########################
##  Command Definitions  ##
###########################

# TaskGraph helper functions
def LTV1_TaskComplete(payload : st.ParamMap):
    LTV1_task_graph.mark_completed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def LTV1_TaskFail(payload : st.ParamMap):
    LTV1_task_graph.mark_failed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))

def MoveToCoord_LTV1_Complete(payload : st.ParamMap):
    st.OnScreenLogMessage("MoveToCoord command complete.", "MM Surface Movement", st.Severity.Info)
    LTV1_TaskComplete(payload)
mm.OnCommandComplete(LTV1, "MoveToCoord", MoveToCoord_LTV1_Complete)

def MoveToCoord_LTV1_Failed(payload : st.ParamMap):
    st.OnScreenLogMessage("MoveToCoord command failed.", "MM Surface Movement", st.Severity.Info)
    LTV1_TaskFail(payload)
    # Example of handling move failure by clearing all tasks, then letting the loop pick up where we left off
    # LTV1_task_graph.clear_all() #wipe existing tasks
mm.OnCommandFail(LTV1, "MoveToCoord", MoveToCoord_LTV1_Failed)

def RotateToAzimuth_LTV1_Complete(payload : st.ParamMap):
    st.OnScreenLogMessage("RotateToAzimuth command complete.", "MM Surface Movement", st.Severity.Info)
    LTV1_TaskComplete(payload)
mm.OnCommandComplete(LTV1, "RotateToAzimuth", RotateToAzimuth_LTV1_Complete)

def RotateToAzimuth_LTV1_Failed(payload : st.ParamMap):
    st.OnScreenLogMessage("RotateToAzimuth command failed.", "MM Surface Movement", st.Severity.Info)
    LTV1_TaskFail(payload)
    # Example of handling move failure by clearing all tasks, then letting the loop pick up where we left off
    # LTV1_task_graph.clear_all() #wipe existing tasks
mm.OnCommandFail(LTV1, "RotateToAzimuth", RotateToAzimuth_LTV1_Failed)

def CameraCapture_LTV1_Complete(payload : st.ParamMap):
    st.OnScreenLogMessage("CameraCapture command complete.", "Mission Manager", st.Severity.Info)
    LTV1_TaskComplete(payload)

    image = st.CapturedImage()
    image.PixelsR = payload.GetParamArray(st.VarType.uint8, "PixelsR")
    image.PixelsG = payload.GetParamArray(st.VarType.uint8, "PixelsG")
    image.PixelsB = payload.GetParamArray(st.VarType.uint8, "PixelsB")
    image.properties.ResolutionX = payload.GetParam(st.VarType.int32, "ResolutionX")
    image.properties.ResolutionY = payload.GetParam(st.VarType.int32, "ResolutionY")
    image.properties.EV = payload.GetParam(st.VarType.double, "Exposure")
    image.properties.FOV = payload.GetParam(st.VarType.double, "FOV")
    ProcessImage(image)

mm.OnCommandComplete(LTV1, "CaptureImage", CameraCapture_LTV1_Complete)

def CameraCapture_LTV1_Failed(payload : st.ParamMap):
    st.OnScreenLogMessage("CameraCapture command failed.", "Mission Manager", st.Severity.Info)
    LTV1_TaskFail(payload)
mm.OnCommandFail(LTV1, "CaptureImage", CameraCapture_LTV1_Failed)
# Not handling failure, on purpose.

################################
##  Mission Manager Commands  ##
################################

# Get initial xy for LTV1 (assume has comms initially)
xy_LTV1, had_comms = ET.GetCurrentXY(LTV1)

waypoint_1 = XY(xy_LTV1.x + 20, xy_LTV1.y)

if(xy_LTV1.x < 0):
    waypoint_1 = XY(xy_LTV1.x - 20, xy_LTV1.y)

waypoint_2 = XY(xy_LTV1.x + 20, xy_LTV1.y + 30)
waypoint_3 = XY(xy_LTV1.x + 20, xy_LTV1.y + 40)

# task = Task(name, Command(entity, xy coord, name))
# taskgraph << task, dependencies (as a list of names, or blank list)

# Moves
move_1 = TG.Task("Move1", Command_MoveToCoord(LTV1, waypoint_1, "Move1"))
LTV1_task_graph.add_task(move_1, [])

move_2 = TG.Task("Move2", Command_MoveToCoord(LTV1, waypoint_2, "Move2"))
LTV1_task_graph.add_task(move_2, ["Move1"])

# Images
exposure = 15.0

# EXAMPLE CODE FOR ADDING PLANNED IMAGE-CAPTURE TASKS
# img_cap1 = TG.Task("Capture1", Command_CaptureImage(LTV1, exposure, "Capture1"))
# LTV1_task_graph.add_task(img_cap1, ["Move1"])

# img_cap2 = TG.Task("Capture2", Command_CaptureImage(LTV1, exposure, "Capture2"))
# LTV1_task_graph.add_task(img_cap2, ["Capture1"])

# cam_turn = TG.Task("camturn", Command_CameraPan(LTV1, 60.0, 11.0, "camturn"))
# LTV1_task_graph.add_task(cam_turn, ["Capture2"])

# img_cap3 = TG.Task("Capture3", Command_CaptureImage(LTV1, exposure, "Capture3"))
# LTV1_task_graph.add_task(img_cap3, ["Capture2"])

# More moves
move_3 = TG.Task("Move3", Command_MoveToCoord(LTV1, waypoint_3, "Move3"))
LTV1_task_graph.add_task(move_3, ["Move2"])

rotate_1 = TG.Task("Rotate_1", Command_RotateToAzimuth(LTV1, 0, "Rotate_1"))
LTV1_task_graph.add_task(rotate_1, ["Move3"])

Scout1_move1 = TG.Task("Move1", Command_MoveToCoord(Scout1, waypoint_1, "Move1"))
Scout1_task_graph.add_task(Scout1_move1, [])

Scout2_move1 = TG.Task("Move1", Command_MoveToCoord(Scout2, waypoint_2, "Move1"))
Scout2_task_graph.add_task(Scout2_move1, [])

#################################
##  Simulation Initialization  ##
#################################

# Wait a bit, then broadcast that the LTVs are starting their movements
time.sleep(5.0)
st.OnScreenLogMessage("Starting movements.", "Mission Manager", st.Severity.Info)


#######################
##  Simulation Loop  ##
#######################

iterator = 0

exit_flag = False
while not exit_flag:
    LoopFreqHz = st.GetThisSystem().GetParam(st.VarType.double, "LoopFreqHz")
    time.sleep(1.0 / LoopFreqHz)
    iterator += 1

    # EXAMPLE: Take a camera image periodically, outside of the task graph
    # if iterator % 500 == 0:
    #     mm.SendCommand(LTV1, "CaptureImage", Command_CaptureImage(LTV1, exposure, "MyImCapture"))

    #NOTE: Can send commands without using taskgraph as well, but will need to wait for 
    # completion manually (mm.OnCommandComplete()) before sending a new command of the 
    # same type to the same entity.
    # azimuth = 150.0 #deg
    # elevation = 10.0 #deg
    # mm.SendCommand(LTV1, "CameraPan", Command_CameraPan(LTV1, azimuth, elevation, ""))


    #NOTE: Here is an example of modifying the task graph based on some condition
    # state_of_charge, had_comms = ET.GetStateOfCharge(LTV1)
    # if(had_comms and state_of_charge < 0.1):
    #     st.OnScreenLogMessage("LTV1 is low on power; rerouting to charging station.", "Mission Manager", st.Severity.Info)
    #     move_task = TG.Task("MoveToCharge", Command_MoveToCoord(LTV1, ET.GetChargingStationXY(), "MoveToCharge"))
    #     LTV1_task_graph.clear_all() #wipe existing tasks
    #     LTV1_task_graph.add_task(move_task, [])

    # LTV1 tasking
    # Example of logging taskgraph status:
    # st.logger_info("LTV1 task status: " + str(LTV1_task_graph.get_status()))

    # Start all unstarted ready-to-start tasks
    for task_id in LTV1_task_graph.pending_tasks:
        task = LTV1_task_graph.get_task(task_id)
        if not task.started:
            received = mm.SendCommand(LTV1, task.command.command_type, task.command)
            if received:
                task.started = True

    for task_id in LTV2_task_graph.pending_tasks:
        task = LTV2_task_graph.get_task(task_id)
        if not task.started:
            received = mm.SendCommand(LTV2, task.command.command_type, task.command)
            if received:
                task.started = True

    for task_id in Scout1_task_graph.pending_tasks:
        task = Scout1_task_graph.get_task(task_id)
        if not task.started:
            received = mm.SendCommand(Scout1, task.command.command_type, task.command)
            if received:
                task.started = True

    for task_id in Scout2_task_graph.pending_tasks:
        task = Scout2_task_graph.get_task(task_id)
        if not task.started:
            received = mm.SendCommand(Scout2, task.command.command_type, task.command)
            if received:
                task.started = True

    # Example of checking for any failures, and clearing all tasks if there was one
    # if len(LTV1_task_graph.failed_tasks) > 0:
    #     LTV1_task_graph.clear_all() #wipe existing tasks
    #     #NOTE might want to do something else here?

    if image_changed:
        # HOW TO SHOW AN IMAGE ON-SCREEN; PROBABLY DEACTIVATE THIS SO IT DOESN'T POP UP WHEN NOT TESTING
        cv2.imshow("Captured Image", img_rgb)
        cv2.waitKey(1)
        image_changed = False

st.leave_sim()
