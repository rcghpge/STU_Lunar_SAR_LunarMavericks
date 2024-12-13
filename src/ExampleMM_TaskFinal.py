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
entities : list[st.Entity] = st.GetThisSystem().GetParamArray(st.VarType.entityRef, "Entities")
LTV1: st.Entity = entities[0]
LTV2: st.Entity = entities[1]
Scout1: st.Entity = entities[2]
Scout2: st.Entity = entities[3]
TruckRover: st.Entity = entities[4]
ExcavatorRover: st.Entity = entities[5]
SamplingRover: st.Entity = entities[6]

# ADDED IN v1.2.1; NECESSARY FOR REACTION-NOT-SET WARNINGS
for en in entities:
    mm.SetupAllCommands(en)

LTV1_task_graph = TG.TaskGraph()
LTV2_task_graph = TG.TaskGraph()
Scout1_task_graph = TG.TaskGraph()
Scout2_task_graph = TG.TaskGraph()
TruckRover_task_graph = TG.TaskGraph()
ExcavatorRover_task_graph = TG.TaskGraph()
SamplingRover_task_graph = TG.TaskGraph()

entity_to_task_graph = {
    LTV1: LTV1_task_graph,
    LTV2: LTV2_task_graph,
    Scout1: Scout1_task_graph,
    Scout2: Scout2_task_graph,
    TruckRover: TruckRover_task_graph,
    ExcavatorRover: ExcavatorRover_task_graph,
    SamplingRover: SamplingRover_task_graph
}

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

def CreateTimerTask(task_name : str, duration_sec : float) -> TG.Task:
    timer_task = TG.Task(task_name)
    timer_task.task_type = "Timer"
    timer_task.timer_duration = duration_sec
    # start time is set whenever the timer task is started in the task graph
    return timer_task

###########################
##  Command Definitions  ##
###########################

# TaskGraph helper functions
def LTV1_TaskComplete(payload : st.ParamMap):
    LTV1_task_graph.mark_completed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def LTV1_TaskFail(payload : st.ParamMap):
    LTV1_task_graph.mark_failed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def LTV2_TaskComplete(payload : st.ParamMap):
    LTV2_task_graph.mark_completed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def LTV2_TaskFail(payload : st.ParamMap):
    LTV2_task_graph.mark_failed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def Scout1_TaskComplete(payload : st.ParamMap):
    Scout1_task_graph.mark_completed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def Scout1_TaskFail(payload : st.ParamMap):
    Scout1_task_graph.mark_failed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def Scout2_TaskComplete(payload : st.ParamMap):
    Scout2_task_graph.mark_completed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def Scout2_TaskFail(payload : st.ParamMap):
    Scout2_task_graph.mark_failed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def ExcavatorRover_TaskComplete(payload : st.ParamMap):
    ExcavatorRover_task_graph.mark_completed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def ExcavatorRover_TaskFail(payload : st.ParamMap):
    ExcavatorRover_task_graph.mark_failed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def TruckRover_TaskComplete(payload : st.ParamMap):
    TruckRover_task_graph.mark_completed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def TruckRover_TaskFail(payload : st.ParamMap):
    TruckRover_task_graph.mark_failed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def SamplingRover_TaskComplete(payload : st.ParamMap):
    SamplingRover_task_graph.mark_completed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))
def SamplingRover_TaskFail(payload : st.ParamMap):
    SamplingRover_task_graph.mark_failed(payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"]))

def General_TaskComplete(payload : st.ParamMap, entity : st.Entity):
    task_id = payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"])
    entity_to_task_graph[entity].mark_completed(task_id)
def General_TaskFail(payload : st.ParamMap, entity : st.Entity):
    task_id = payload.GetParam(st.VarType.string, ["Orig_Cmd", "TaskID"])
    entity_to_task_graph[entity].mark_completed(task_id)

# MOVING

def MoveToCoord_Complete(payload : st.ParamMap, en : st.Entity):
    st.OnScreenLogMessage(f"{en.getName()}: MoveToCoord command complete.", "MM Surface Movement", st.Severity.Info)
    General_TaskComplete(payload, en)
mm.OnCommandComplete(LTV1, "MoveToCoord", lambda payload : MoveToCoord_Complete(payload, LTV1))
mm.OnCommandComplete(LTV2, "MoveToCoord", lambda payload : MoveToCoord_Complete(payload, LTV2))
mm.OnCommandComplete(Scout1, "MoveToCoord", lambda payload : MoveToCoord_Complete(payload, Scout1))
mm.OnCommandComplete(Scout2, "MoveToCoord", lambda payload : MoveToCoord_Complete(payload, Scout2))
#NOTE: could move the rest of the complete/failed reaction funcs to this compacted version

def MoveToCoord_Failed(payload : st.ParamMap, en : st.Entity):
    if payload.HasParam(st.VarType.string, "Reason"):
        reason = payload.GetParam(st.VarType.string, "Reason")
        st.OnScreenLogMessage(f"{en.getName()}: MoveToCoord command failed. Reason: {reason}", "MM Surface Movement", st.Severity.Warning)
        if reason == "Hit Obstacle":
            st.OnScreenLogMessage(f"{en.getName()}: Moving away from obstacle now.", "MM Surface Movement", st.Severity.Warning)
            #Code to handle this, probably by moving away a bit and then moving around the obstacle
            currentxy, _ = ET.GetCurrentXY(en)
            rel_vecs, radii, _ = ET.GetLidarObstacles(en)
            closest_dist = 9999999
            closest_idx = -1
            for i in range(len(rel_vecs)):
                dist = np.linalg.norm(rel_vecs[i]) - radii[i]
                if(dist < closest_dist):
                    closest_dist = dist
                    closest_idx = i
            
            closest_rel_vec = np.asarray(rel_vecs[closest_idx])
            closest_radius = radii[closest_idx]
            
            # Move away from the obstacle
            currentcoord = currentxy.toCoord()
            currentLoc = currentcoord.getLoc()
            # move away 2x radius
            away_from_obstacle_loc = currentLoc - (closest_radius * 2.0 * closest_rel_vec)/np.linalg.norm(closest_rel_vec)
            away_from_obstacle_xy = CoordToXY(st.PlanetUtils.Coord(away_from_obstacle_loc, currentcoord.getRot(), currentcoord.getRadius()))

            move_from_obstacle = TG.Task("MoveFromObstacle", Command_MoveToCoord(en, away_from_obstacle_xy, "MoveFromObstacle")) 
            entity_to_task_graph[en].add_task(move_from_obstacle, [])
            # Continue with search?
    else:
        st.OnScreenLogMessage(f"{en.getName()}: MoveToCoord command failed.", "MM Surface Movement", st.Severity.Error)
    General_TaskFail(payload, en)
    # Example of handling move failure by clearing all tasks, then letting the loop pick up where we left off
    # LTV1_task_graph.clear_all() #wipe existing tasks
mm.OnCommandFail(LTV1, "MoveToCoord", lambda payload : MoveToCoord_Failed(payload, LTV1))
mm.OnCommandFail(LTV2, "MoveToCoord", lambda payload : MoveToCoord_Failed(payload, LTV2))
mm.OnCommandFail(Scout1, "MoveToCoord", lambda payload : MoveToCoord_Failed(payload, Scout1))
mm.OnCommandFail(Scout2, "MoveToCoord", lambda payload : MoveToCoord_Failed(payload, Scout2))
#NOTE: could move the rest of the complete/failed reaction funcs to this compacted version

# STOPPING

def Stop_Complete(payload : st.ParamMap, en : st.Entity):
    st.OnScreenLogMessage(f"{en.getName()}: Stop command complete.", "MM Surface Movement", st.Severity.Info)
    General_TaskComplete(payload, en)
mm.OnCommandComplete(LTV1, "Stop", lambda payload : Stop_Complete(payload, LTV1))
mm.OnCommandComplete(LTV2, "Stop", lambda payload : Stop_Complete(payload, LTV2))
#TODO could add the rest of the entities here

def Stop_Failed(payload : st.ParamMap, en : st.Entity):
    st.OnScreenLogMessage(f"{en.getName()}: Stop command failed.", "MM Surface Movement", st.Severity.Error)
    General_TaskFail(payload, en)
mm.OnCommandFail(LTV1, "Stop", lambda payload : Stop_Failed(payload, LTV1))
mm.OnCommandFail(LTV2, "Stop", lambda payload : Stop_Failed(payload, LTV2))
#TODO could add the rest of the entities here

# ROTATING TO AZIMUTH

def RotateToAzimuth_LTV1_Complete(payload : st.ParamMap):
    st.OnScreenLogMessage(f"{LTV1.getName()}: RotateToAzimuth command complete.", "MM Surface Movement", st.Severity.Info)
    LTV1_TaskComplete(payload)
mm.OnCommandComplete(LTV1, "RotateToAzimuth", RotateToAzimuth_LTV1_Complete)

def RotateToAzimuth_LTV1_Failed(payload : st.ParamMap):
    st.OnScreenLogMessage(f"{LTV1.getName()}: RotateToAzimuth command failed.", "MM Surface Movement", st.Severity.Error)
    LTV1_TaskFail(payload)
    # Example of handling move failure by clearing all tasks, then letting the loop pick up where we left off
    # LTV1_task_graph.clear_all() #wipe existing tasks
mm.OnCommandFail(LTV1, "RotateToAzimuth", RotateToAzimuth_LTV1_Failed)

def CameraCapture_LTV1_Complete(payload : st.ParamMap):
    st.OnScreenLogMessage(f"{LTV1.getName()}: CameraCapture command complete.", "Mission Manager", st.Severity.Info)
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
    st.OnScreenLogMessage(f"{LTV1.getName()}: CameraCapture command failed.", "Mission Manager", st.Severity.Error)
    LTV1_TaskFail(payload)
mm.OnCommandFail(LTV1, "CaptureImage", CameraCapture_LTV1_Failed)
# Not handling failure, on purpose.

def MoveToCoord_ExcavatorRover_Complete(payload : st.ParamMap):
    st.OnScreenLogMessage(f"{ExcavatorRover.getName()}: MoveToCoord command complete.", "MM Surface Movement", st.Severity.Info)
    ExcavatorRover_TaskComplete(payload)
mm.OnCommandComplete(ExcavatorRover, "MoveToCoord", MoveToCoord_ExcavatorRover_Complete)

def MoveToCoord_ExcavatorRover_Failed(payload : st.ParamMap):
    st.OnScreenLogMessage(f"{ExcavatorRover.getName()}: MoveToCoord command failed.", "MM Surface Movement", st.Severity.Error)
    ExcavatorRover_TaskFail(payload)
    # Example of handling move failure by clearing all tasks, then letting the loop pick up where we left off
    # LTV2_task_graph.clear_all() #wipe existing tasks
mm.OnCommandFail(ExcavatorRover, "MoveToCoord", MoveToCoord_ExcavatorRover_Failed)

def MoveToCoord_TruckRover_Complete(payload : st.ParamMap):
    st.OnScreenLogMessage(f"{TruckRover.getName()}: MoveToCoord command complete.", "MM Surface Movement", st.Severity.Info)
    TruckRover_TaskComplete(payload)
mm.OnCommandComplete(TruckRover, "MoveToCoord", MoveToCoord_TruckRover_Complete)

def MoveToCoord_TruckRover_Failed(payload : st.ParamMap):
    st.OnScreenLogMessage(f"{TruckRover.getName()}: MoveToCoord command failed.", "MM Surface Movement", st.Severity.Error)
    TruckRover_TaskFail(payload)
    # Example of handling move failure by clearing all tasks, then letting the loop pick up where we left off
    # LTV2_task_graph.clear_all() #wipe existing tasks
mm.OnCommandFail(TruckRover, "MoveToCoord", MoveToCoord_TruckRover_Failed)

def MoveToCoord_SamplingRover_Complete(payload : st.ParamMap):
    st.OnScreenLogMessage(f"{SamplingRover.getName()}: MoveToCoord command complete.", "MM Surface Movement", st.Severity.Info)
    SamplingRover_TaskComplete(payload)
mm.OnCommandComplete(SamplingRover, "MoveToCoord", MoveToCoord_SamplingRover_Complete)

def MoveToCoord_SamplingRover_Failed(payload : st.ParamMap):
    st.OnScreenLogMessage(f"{SamplingRover.getName()}: MoveToCoord command failed.", "MM Surface Movement", st.Severity.Error)
    SamplingRover_TaskFail(payload)
    # Example of handling move failure by clearing all tasks, then letting the loop pick up where we left off
    # LTV2_task_graph.clear_all() #wipe existing tasks
mm.OnCommandFail(SamplingRover, "MoveToCoord", MoveToCoord_SamplingRover_Failed)

# Pick up antenna:
#TODO only LTV1 can pick up antennae
def PickUpAntenna_LTV1_Complete(payload: st.ParamMap):
    st.OnScreenLogMessage(f"{LTV1.getName()}: PickUpAntenna command complete.", "Mission Manager", st.Severity.Info)
    LTV1_TaskComplete(payload)
mm.OnCommandComplete(LTV1, "PickUpAntenna", PickUpAntenna_LTV1_Complete)

def PickUpAntenna_LTV1_Failed(payload: st.ParamMap):
    st.OnScreenLogMessage(f"{LTV1.getName()}: PickUpAntenna command failed.", "Mission Manager", st.Severity.Error)
    LTV1_TaskFail(payload)
mm.OnCommandFail(LTV1, "PickUpAntenna", PickUpAntenna_LTV1_Failed)

# Place down antenna:
def PlaceDownAntenna_LTV1_Complete(payload: st.ParamMap):
    st.OnScreenLogMessage(f"{LTV1.getName()}: PlaceDownAntenna command complete.", "Mission Manager", st.Severity.Info)
    LTV1_TaskComplete(payload)
mm.OnCommandComplete(LTV1, "PlaceDownAntenna", PlaceDownAntenna_LTV1_Complete)

def PlaceDownAntenna_LTV1_Failed(payload: st.ParamMap):
    st.OnScreenLogMessage(f"{LTV1.getName()}: PlaceDownAntenna command failed.", "Mission Manager", st.Severity.Error)
    LTV1_TaskFail(payload)
mm.OnCommandFail(LTV1, "PlaceDownAntenna", PlaceDownAntenna_LTV1_Failed)

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


# Pick up an antenna, drive away with it, then place it down
antenna1_initialLoc = ET.GetAntennaXY(1)
NewAntennaPlacement = XY(antenna1_initialLoc.x + 100, antenna1_initialLoc.y + 20)
waypoint_ltv1_2 = XY(antenna1_initialLoc.x + 300, antenna1_initialLoc.y + 10)

LTV1_move_to_antenna = TG.Task("MoveToAntenna", Command_MoveToCoord(LTV1, antenna1_initialLoc, "MoveToAntenna"))
LTV1_get_antenna = TG.Task("PickUpAntenna", Command_PickUpAntenna(LTV1, "PickUpAntenna"))
LTV1_move1 = TG.Task("Move1", Command_MoveToCoord(LTV1, NewAntennaPlacement, "Move1"))
LTV1_place_antenna = TG.Task("PlaceDownAntenna", Command_PlaceDownAntenna(LTV1, "PlaceDownAntenna"))
LTV1_move2 = TG.Task("Move2", Command_MoveToCoord(LTV1, waypoint_ltv1_2, "Move2"))

LTV1_task_graph.add_task(LTV1_move_to_antenna, [])
LTV1_task_graph.add_task(LTV1_get_antenna, ["MoveToAntenna"])
LTV1_task_graph.add_task(LTV1_move1, ["PickUpAntenna"])
LTV1_task_graph.add_task(LTV1_place_antenna, ["Move1"])
LTV1_task_graph.add_task(LTV1_move2, ["PlaceDownAntenna"])


# Demonstrate stopping
LTV2_move_1 = TG.Task("Move1", Command_MoveToCoord(LTV2, waypoint_1, "Move1"))
LTV2_stop1 = TG.Task("Stop1", Command_Stop(LTV2, "Stop1"))
LTV2_move_2 = TG.Task("Move2", Command_MoveToCoord(LTV2, waypoint_2, "Move2"))

LTV2_task_graph.add_task(LTV2_move_1, [])
LTV2_task_graph.add_task(CreateTimerTask("TimeBeforeStop", 5.0), [])
LTV2_task_graph.add_task(LTV2_stop1, ["TimeBeforeStop"])
# LTV2_task_graph.add_task(LTV2_move_2, ["Stop1"])

# Move scout rovers to waypoints
waypoint_far = XY(antenna1_initialLoc.x + 20000, antenna1_initialLoc.y + 40)
Scout1_move1 = TG.Task("Move1", Command_MoveToCoord(Scout1, waypoint_1, "Move1"))
Scout1_move1 = TG.Task("MoveFar", Command_MoveToCoord(Scout1, waypoint_far, "MoveFar"))
Scout1_task_graph.add_task(Scout1_move1, [])
Scout1_task_graph.add_task(Scout1_move1, ["Move1"])

Scout2_move1 = TG.Task("Move1", Command_MoveToCoord(Scout2, waypoint_2, "Move1"))
Scout2_task_graph.add_task(Scout2_move1, [])

# Drive truck to charging station, charge, then drive away
waypoint_charge = ET.GetChargingStationXY()
waypoint_truck = XY(waypoint_charge.x + 50, waypoint_charge.y + 20)

TruckRover_move_charge = TG.Task("MoveCharge", Command_MoveToCoord(TruckRover, waypoint_charge, "MoveCharge"))
TruckRover_move1 = TG.Task("Move1", Command_MoveToCoord(TruckRover, waypoint_truck, "Move1"))

TruckRover_task_graph.add_task(TruckRover_move_charge, [])
TruckRover_task_graph.add_task(CreateTimerTask("WaitWhileCharging", 15.0), ["MoveCharge"])
TruckRover_task_graph.add_task(TruckRover_move1, ["WaitWhileCharging"])


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

crash_site_loc = XY(0, 0)
crash_site_found = False

exit_flag = False
while not exit_flag:
    LoopFreqHz = st.GetThisSystem().GetParam(st.VarType.double, "LoopFreqHz")
    time.sleep(1.0 / LoopFreqHz)
    iterator += 1

    if not crash_site_found:
        for en in entities:
            found, xy, had_comms = ET.GetTargetScanStatus(en)
            if had_comms and found:
                st.OnScreenLogMessage(f"{en.getName()} found target at {xy.x}, {xy.y}", "Mission Manager", st.Severity.Info)
                crash_site_loc = xy
                crash_site_found = True
                #NOTE: should send LTV1 to crash site with >50% battery remaining to rescue
                # battery_fraction, had_comms = ET.GetStateOfCharge(LTV1)
                # if had_comms and battery_fraction > 0.5:
                #     st.OnScreenLogMessage(f"{LTV1.getName()} has enough battery to go to crash site.", "Mission Manager", st.Severity.Info)

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
            if task.task_type == "Command":
                received = mm.SendCommand(LTV1, task.command.command_type, task.command)
                if received:
                    task.started = True
            elif task.task_type == "Timer":
                task.start_time = st.SimGlobals_SimClock_GetTimeNow()
                task.started = True
        else: # task has started
            if task.task_type == "Timer":
                if st.SimGlobals_SimClock_GetTimeNow().as_datetime() - task.start_time.as_datetime() > datetime.timedelta(seconds=task.timer_duration):
                    LTV1_task_graph.mark_completed(task_id)
    
    for task_id in LTV2_task_graph.pending_tasks:
        task = LTV2_task_graph.get_task(task_id)
        if not task.started:
            if task.task_type == "Command":
                received = mm.SendCommand(LTV2, task.command.command_type, task.command)
                if received:
                    task.started = True
            elif task.task_type == "Timer":
                task.start_time = st.SimGlobals_SimClock_GetTimeNow()
                task.started = True
        else: # task has started
            if task.task_type == "Timer":
                if st.SimGlobals_SimClock_GetTimeNow().as_datetime() - task.start_time.as_datetime() > datetime.timedelta(seconds=task.timer_duration):
                    LTV2_task_graph.mark_completed(task_id)
    
    for task_id in Scout1_task_graph.pending_tasks:
        task = Scout1_task_graph.get_task(task_id)
        if not task.started:
            if task.task_type == "Command":
                received = mm.SendCommand(Scout1, task.command.command_type, task.command)
                if received:
                    task.started = True
            elif task.task_type == "Timer":
                task.start_time = st.SimGlobals_SimClock_GetTimeNow()
                task.started = True
        else: # task has started
            if task.task_type == "Timer":
                if st.SimGlobals_SimClock_GetTimeNow().as_datetime() - task.start_time.as_datetime() > datetime.timedelta(seconds=task.timer_duration):
                    Scout1_task_graph.mark_completed(task_id)

    for task_id in Scout2_task_graph.pending_tasks:
        task = Scout2_task_graph.get_task(task_id)
        if not task.started:
            if task.task_type == "Command":
                received = mm.SendCommand(Scout2, task.command.command_type, task.command)
                if received:
                    task.started = True
            elif task.task_type == "Timer":
                task.start_time = st.SimGlobals_SimClock_GetTimeNow()
                task.started = True
        else: # task has started
            if task.task_type == "Timer":
                if st.SimGlobals_SimClock_GetTimeNow().as_datetime() - task.start_time.as_datetime() > datetime.timedelta(seconds=task.timer_duration):
                    Scout2_task_graph.mark_completed(task_id)

    for task_id in TruckRover_task_graph.pending_tasks:
        task = TruckRover_task_graph.get_task(task_id)
        if not task.started:
            if task.task_type == "Command":
                received = mm.SendCommand(TruckRover, task.command.command_type, task.command)
                if received:
                    task.started = True
            elif task.task_type == "Timer":
                task.start_time = st.SimGlobals_SimClock_GetTimeNow()
                task.started = True
        else: # task has started
            if task.task_type == "Timer":
                if st.SimGlobals_SimClock_GetTimeNow().as_datetime() - task.start_time.as_datetime() > datetime.timedelta(seconds=task.timer_duration):
                    TruckRover_task_graph.mark_completed(task_id)

    for task_id in ExcavatorRover_task_graph.pending_tasks:
        task = ExcavatorRover_task_graph.get_task(task_id)
        if not task.started:
            if task.task_type == "Command":
                received = mm.SendCommand(ExcavatorRover, task.command.command_type, task.command)
                if received:
                    task.started = True
            elif task.task_type == "Timer":
                task.start_time = st.SimGlobals_SimClock_GetTimeNow()
                task.started = True
        else: # task has started
            if task.task_type == "Timer":
                if st.SimGlobals_SimClock_GetTimeNow().as_datetime() - task.start_time.as_datetime() > datetime.timedelta(seconds=task.timer_duration):
                    ExcavatorRover_task_graph.mark_completed(task_id)

    for task_id in SamplingRover_task_graph.pending_tasks:
        task = SamplingRover_task_graph.get_task(task_id)
        if not task.started:
            if task.task_type == "Command":
                received = mm.SendCommand(SamplingRover, task.command.command_type, task.command)
                if received:
                    task.started = True
            elif task.task_type == "Timer":
                task.start_time = st.SimGlobals_SimClock_GetTimeNow()
                task.started = True
        else: # task has started
            if task.task_type == "Timer":
                if st.SimGlobals_SimClock_GetTimeNow().as_datetime() - task.start_time.as_datetime() > datetime.timedelta(seconds=task.timer_duration):
                    SamplingRover_task_graph.mark_completed(task_id)

    # Example of checking for any failures, and clearing all tasks if there was one
    # if len(LTV1_task_graph.failed_tasks) > 0:
    #     LTV1_task_graph.clear_all() #wipe existing tasks
    #     #NOTE might want to do something else here?

    # if image_changed:
    #     # HOW TO SHOW AN IMAGE ON-SCREEN; PROBABLY DEACTIVATE THIS SO IT DOESN'T POP UP WHEN NOT TESTING
    #     cv2.imshow("Captured Image", img_rgb)
    #     cv2.waitKey(1)
    #     image_changed = False

st.leave_sim()
