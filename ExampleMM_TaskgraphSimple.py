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

#############################
##  Mission Manager Setup  ##
#############################

# Get all entities participating in the search
entities = st.GetThisSystem().GetParamArray(st.VarType.entityRef, "Entities")
LTV1: st.Entity = entities[0]
LTV2: st.Entity = entities[1]

LTV1_task_graph = TG.TaskGraph()
LTV2_task_graph = TG.TaskGraph()


###########################
##  Command Definitions  ##
###########################

# TaskGraph helper functions
def LTV1_TaskComplete(payload : st.ParamMap):
    LTV1_task_graph.mark_completed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def LTV1_TaskFail(payload : st.ParamMap):
    LTV1_task_graph.mark_failed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))

##############################
##  Move commands for LTV1  ##
##############################

def MoveToCoord_LTV1_Complete(payload : st.ParamMap):
    st.OnScreenLogMessage("MoveToCoord command complete.", "Surface Movement", st.Severity.Info)
    LTV1_TaskComplete(payload)
mm.OnCommandComplete(LTV1, "MoveToCoord", MoveToCoord_LTV1_Complete)

def MoveToCoord_LTV1_Failed(payload : st.ParamMap):
    st.OnScreenLogMessage("MoveToCoord command failed.", "Surface Movement", st.Severity.Info)
    LTV1_TaskFail(payload)
mm.OnCommandFail(LTV1, "MoveToCoord", MoveToCoord_LTV1_Failed)

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

move_1 = TG.Task("Move1", Command_MoveToCoord(LTV1, waypoint_1, "Move1"))
LTV1_task_graph.add_task(move_1, [])

move_2 = TG.Task("Move2", Command_MoveToCoord(LTV1, waypoint_2, "Move2"))
LTV1_task_graph.add_task(move_2, ["Move1"])

move_3 = TG.Task("Move3", Command_MoveToCoord(LTV1, waypoint_3, "Move3"))
LTV1_task_graph.add_task(move_3, ["Move2"])

#################################
##  Simulation Initialization  ##
#################################

# Wait a bit, then broadcast that the LTVs are starting their movements
time.sleep(5.0)
st.OnScreenLogMessage("Starting LTV movements.", "Mission Manager", st.Severity.Info)

#######################
##  Simulation Loop  ##
#######################

exit_flag = False
while not exit_flag:
    LoopFreqHz = st.GetThisSystem().GetParam(st.VarType.double, "LoopFreqHz")
    time.sleep(1.0 / LoopFreqHz)

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

st.leave_sim()
