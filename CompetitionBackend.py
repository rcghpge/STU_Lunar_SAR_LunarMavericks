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
# import MissionManagerFuncs as MM
# mm = MM.MissionManager()
import API.SurfaceMovement as SM
import API.EntityTelemetry as ET
# ^ NECESSARY STU IMPORTS

sim_start_time : st.timestamp = st.SimGlobals_SimClock_GetTimeNow()

every_en = st.GetThisSystem().GetParamArray(st.VarType.entityRef, "Entities")

# Get planet
planet: st.Entity = st.GetThisSystem().GetParam(st.VarType.entityRef, "Planet")


# Define entities
LTV1 = every_en[0]
LTV2 = every_en[1]
ScoutRover1 = every_en[2]
ScoutRover2 = every_en[3]
#EVA1 = every_en[4]
#EVA2 = every_en[5]

# Get all entities participating in the search

# Set up "mover" objects for all entities
mover_LTV1 = SM.SurfaceMover(LTV1, planet)
mover_LTV2 = SM.SurfaceMover(LTV2, planet)
mover_ScoutRover1 = SM.SurfaceMover(ScoutRover1, planet)
mover_ScoutRover2 = SM.SurfaceMover(ScoutRover2, planet)
#mover_EVA1 = SM.SurfaceMover(EVA1, planet)
#mover_EVA2 = SM.SurfaceMover(EVA2, planet)


charging_station: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "ChargingStation")
power_assembly: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "PowerAssembly")

#######################
##  Simulation Loop  ##
#######################

CHARGING_RADIUS_M = 10.0

exit_flag = False
while not exit_flag:
    LoopFreqHz = st.GetThisSystem().GetParam(st.VarType.double, "LoopFreqHz")
    time.sleep(1.0 / LoopFreqHz)

    ### Nominal sim code ###

    # Get the current state of the entities
    LTV1_state, LTV1_has_comms = ET.GetMovementState(LTV1)
    LTV2_state, LTV2_has_comms = ET.GetMovementState(LTV2)
    ScoutRover1_state, ScoutRover1_has_comms = ET.GetMovementState(ScoutRover1)
    ScoutRover2_state, ScoutRover2_has_comms = ET.GetMovementState(ScoutRover2)

    # Check if the entities are moving
    LTV1_is_moving, LTV1_has_comms = ET.IsMoving(LTV1)
    LTV2_is_moving, LTV2_has_comms = ET.IsMoving(LTV2)
    ScoutRover1_is_moving, ScoutRover1_has_comms = ET.IsMoving(ScoutRover1)
    ScoutRover2_is_moving, ScoutRover2_has_comms = ET.IsMoving(ScoutRover2)

    # Check if the entities have comms
    LTV1_has_comms = ET.HasComms(LTV1)
    LTV2_has_comms = ET.HasComms(LTV2)
    ScoutRover1_has_comms = ET.HasComms(ScoutRover1)
    ScoutRover2_has_comms = ET.HasComms(ScoutRover2)

    # Check if the entities are at the charging station
    LTV1_at_charging = False
    LTV2_at_charging = False
    ScoutRover1_at_charging = False
    ScoutRover2_at_charging = False

    LTV1_xy, LTV1_has_comms = ET.GetCurrentXY(LTV1)
    LTV2_xy, LTV2_has_comms = ET.GetCurrentXY(LTV2)
    ScoutRover1_xy, ScoutRover1_has_comms = ET.GetCurrentXY(ScoutRover1)
    ScoutRover2_xy, ScoutRover2_has_comms = ET.GetCurrentXY(ScoutRover2)

    charging_xy = ET.GetChargingStationXY()

    if ((LTV1_xy.x - charging_xy.x) ** 2 + (LTV1_xy.y - charging_xy.y) ** 2) < CHARGING_RADIUS_M ** 2:
        LTV1_at_charging = True

    if ((LTV2_xy.x - charging_xy.x) ** 2 + (LTV2_xy.y - charging_xy.y) ** 2) < CHARGING_RADIUS_M ** 2:
        LTV2_at_charging = True

    if ((ScoutRover1_xy.x - charging_xy.x) ** 2 + (ScoutRover1_xy.y - charging_xy.y) ** 2) < CHARGING_RADIUS_M ** 2:
        ScoutRover1_at_charging = True

    if ((ScoutRover2_xy.x - charging_xy.x) ** 2 + (ScoutRover2_xy.y - charging_xy.y) ** 2) < CHARGING_RADIUS_M ** 2:
        ScoutRover2_at_charging = True

    # Check if the entities are at the crash site
    LTV1_at_crash = False
    LTV2_at_crash = False
    ScoutRover1_at_crash = False
    ScoutRover2_at_crash = False

    crash_xy = ET.GetCrashSiteXY()

    if ((LTV1_xy.x - crash_xy.x) ** 2 + (LTV1_xy.y - crash_xy.y) ** 2) < CHARGING_RADIUS_M ** 2:
        LTV1_at_crash = True

    if ((LTV2_xy.x - crash_xy.x) ** 2 + (LTV2_xy.y - crash_xy.y) ** 2) < CHARGING_RADIUS_M ** 2:
        LTV2_at_crash = True

    if ((ScoutRover1_xy.x - crash_xy.x) ** 2 + (ScoutRover1_xy.y - crash_xy.y) ** 2) < CHARGING_RADIUS_M ** 2:
        ScoutRover1_at_crash = True

    if ((ScoutRover2_xy.x - crash_xy.x) ** 2 + (ScoutRover2_xy.y - crash_xy.y) ** 2) < CHARGING_RADIUS_M ** 2:
        ScoutRover2_at_crash = True

    # (For initial submission: Any robot detects the crash site)
    # (For full submission: LTV with enough resources has reached the crash site)
    # For now, just check if any robot is at the crash site         

    # Charging
    for en in every_en:
        en_xy, _ = ET.GetCurrentXY(en)
        charging_xy = ET.GetChargingStationXY()

        edge_list = ["ChargingStation_LTV1", 
                    "ChargingStation_LTV2", 
                    "ChargingStation_ScoutRover1", 
                    "ChargingStation_ScoutRover2", 
                    "Battery_LTV1", 
                    "Battery_LTV2", 
                    "ChargingStation_EVA1", 
                    "ChargingStation_EVA2", 
                    "Tank1_EVA1", 
                    "Tank1_EVA2"]
        
        for edge in edge_list:
            en_from = power_assembly.GetParam(st.VarType.entityRef, ["#Assembly", "Edges", edge, "From"])
            en_to = power_assembly.GetParam(st.VarType.entityRef, ["#Assembly", "Edges", edge, "To"])
            if en_from == charging_station and en_to == en:
                # Distance check
                if ((en_xy.x - charging_xy.x) ** 2 + (en_xy.y - charging_xy.y) ** 2) < CHARGING_RADIUS_M ** 2:
                    power_assembly.SetParam(st.VarType.bool, ["#Assembly", "Edges", edge, "IsActive"], True)
                else:
                    power_assembly.SetParam(st.VarType.bool, ["#Assembly", "Edges", edge, "IsActive"], False)

    ### Sim end condition checking ###
    # Check whether the challenge end condition has been met
    # (For initial submission: Any robot detects the crash site)
    # (For full submission: LTV with enough resources has reached the crash site)

    end_condition = True

    any_robot_reached_crash_site = False

    for en in every_en:
        target_found, target_xy, had_comms = ET.GetTargetScanStatus(en)
        if(target_found):
            any_robot_reached_crash_site = True

    if(not any_robot_reached_crash_site):
        end_condition = False

    if(end_condition):
        st.SimGlobals_SimClock_Freeze()
        st.OnScreenLogMessage("Sim end conditions met; freezing sim and recording results.", 
                              "Competition Backend", st.Severity.Info)
        sim_end_time : st.timestamp = st.SimGlobals_SimClock_GetTimeNow()
        #TODO this may not work
        sim_duration = sim_end_time.as_datetime() - sim_start_time.as_datetime()
        st.OnScreenLogMessage("Time before complete: " + str(sim_duration), 
                              "Competition Backend", st.Severity.Info)
        exit_flag = True

while(True):
    st.OnScreenAlert("Sim complete; time elapsed: " + str(sim_duration), 
                              "Sim Complete Stuff", st.Severity.Info)
    time.sleep(0.5)

st.leave_sim()
