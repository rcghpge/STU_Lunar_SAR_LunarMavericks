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
import API.EntityTelemetry2 as ET
import TaskGraph as TG
import time

# Initialize MissionManager
mm = MM.MissionManager()

#############################
##  Mission Manager Setup  ##
#############################

# Get all entities participating in the search
entities = st.GetThisSystem().GetParamArray(st.VarType.entityRef, "Entities")
LTV1: st.Entity = entities[0]
LTV2: st.Entity = entities[1]

# Initialize TaskGraphs for LTV1 and LTV2
LTV1_task_graph = TG.TaskGraph()
LTV2_task_graph = TG.TaskGraph()

###########################
##  Command Definitions  ##
###########################

# Helper functions for task completion
def LTV1_TaskComplete(payload: st.ParamMap):
    task_id = payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"])
    LTV1_task_graph.mark_completed(task_id)

def LTV1_TaskFail(payload: st.ParamMap):
    task_id = payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"])
    LTV1_task_graph.mark_failed(task_id)

##############################
##  Move commands for LTV1  ##
##############################

def MoveToCoord_LTV1_Complete(payload: st.ParamMap):
    st.OnScreenLogMessage("MoveToCoord command complete.", "Surface Movement", st.Severity.Info)
    LTV1_TaskComplete(payload)

mm.OnCommandComplete(LTV1, "MoveToCoord", callback=MoveToCoord_LTV1_Complete)

def MoveToCoord_LTV1_Failed(payload: st.ParamMap):
    st.OnScreenLogMessage("MoveToCoord command failed.", "Surface Movement", st.Severity.Info)
    LTV1_TaskFail(payload)

mm.OnCommandFail(LTV1, "MoveToCoord", MoveToCoord_LTV1_Failed)


################################
##  Mission Manager Commands  ##
################################

# Get initial coordinates for LTV1 and set up waypoints
xy_LTV1, had_comms = ET.GetCurrentXY(LTV1)
waypoint_1 = XY(xy_LTV1.x + 20, xy_LTV1.y)
waypoint_2 = XY(xy_LTV1.x + 20, xy_LTV1.y + 30)
waypoint_3 = XY(xy_LTV1.x + 20, xy_LTV1.y + 40)

if xy_LTV1.x < 0:
    waypoint_1 = XY(xy_LTV1.x - 20, xy_LTV1.y)

# Define tasks and dependencies
move_1 = TG.Task("Move1", Command_MoveToCoord(LTV1, waypoint_1, "Move1"))
LTV1_task_graph.add_task(move_1, [])

move_2 = TG.Task("Move2", Command_MoveToCoord(LTV1, waypoint_2, "Move2"))
LTV1_task_graph.add_task(move_2, ["Move1"])

# Optional camera pan and capture tasks
camera_1 = TG.Task("CameraPan", Command_CameraPan(LTV1, 12, 15, "CameraPan"))
LTV1_task_graph.add_task(camera_1, ["Move2"])

camera_2 = TG.Task("CameraCapture", Command_CaptureImage(LTV1, 4, "CameraCapture"))
LTV1_task_graph.add_task(camera_2, ["CameraPan"])

move_3 = TG.Task("Move3", Command_MoveToCoord(LTV1, waypoint_3, "Move3"))
LTV1_task_graph.add_task(move_3, ["CameraCapture"])

#################################
##  Simulation Initialization  ##
#################################

# Start LTV movement after delay
time.sleep(5.0)
st.OnScreenLogMessage("Starting LTV movements.", "Mission Manager", st.Severity.Info)

#######################
##  Simulation Loop  ##
#######################

exit_flag = False
while not exit_flag:
    LoopFreqHz = st.GetThisSystem().GetParam(st.VarType.double, "LoopFreqHz")
    time.sleep(1.0 / LoopFreqHz)

    # Monitor task graph status and check for pending tasks
    for task_id in LTV1_task_graph.pending_tasks:
        task = LTV1_task_graph.get_task(task_id)
        if not task.started:
            received = mm.SendCommand(LTV1, task.command.command_type, task.command)
            if received:
                task.started = True
                st.OnScreenLogMessage(f"Task {task_id} started for LTV1.", "Task Graph", st.Severity.Info)

    # Conditional task graph modification based on entity state (e.g., low power)
    state_of_charge, had_comms = ET.GetStateOfCharge(LTV1)
    if had_comms and state_of_charge < 0.1:
        st.OnScreenLogMessage("LTV1 is low on power; rerouting to charging station.", "Mission Manager", st.Severity.Info)
        move_task = TG.Task("MoveToCharge", Command_MoveToCoord(LTV1, ET.GetChargingStationXY(), "MoveToCharge"))
        LTV1_task_graph.clear_all()  # Clear existing tasks
        LTV1_task_graph.add_task(move_task, [])
        continue  # Skip remaining tasks this loop iteration

# Exiting simulation
st.leave_sim()
