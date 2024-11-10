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
import API.SurfaceMovement as SM
import API.EntityTelemetry as ET
import API.MissionManagerFuncs as MM

# Initialize the MissionManager
mm = MM.MissionManager()

# Initialize simulation start time
sim_start_time: st.timestamp = st.SimGlobals_SimClock_GetTimeNow()

# Checking if the simulation is running
if not st.SimGlobals_IsSimRunning():
    st.OnScreenLogMessage("Simulation is not running; exiting script.", "Competition Backend", st.Severity.Error)
    exit(1)

# Get the current system and all entities
st.GetThisSystem()

try:
    power_assembly: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "PowerAssembly")
except RuntimeError:
    power_assembly = None
    st.OnScreenLogMessage("PowerAssembly parameter not found in SimEntity.", "CompetitionBackend", st.Severity.Warning)

st.GetSimEntity()

# Get all entities and the planet
every_en = st.GetThisSystem().GetParamArray(st.VarType.entityRef, "Entities")
planet: st.Entity = st.GetThisSystem().GetParam(st.VarType.entityRef, "Planet")

# Initialize power assembly and charging station
charging_station: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "ChargingStation")
power_assembly: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "PowerAssembly")

# Constants
CHARGING_RADIUS_M = 10.0
LoopFreqHz = st.GetThisSystem().GetParam(st.VarType.double, "LoopFreqHz")

# Dynamically identify LTV entities and create mover objects for each one
LTVs = [en for en in every_en if en.GetParam(st.VarType.string, "Type") == "LTV"]
movers = [SM.SurfaceMover(ltv, planet) for ltv in LTVs]

# Edge list for charging logic
edge_list = [
    "ChargingStation_LTV1", "ChargingStation_LTV2", 
    "ChargingStation_ScoutRover1", "ChargingStation_ScoutRover2", 
    "Battery_LTV1", "Battery_LTV2", 
    "ChargingStation_EVA1", "ChargingStation_EVA2", 
    "Tank1_EVA1", "Tank1_EVA2"
]

# Mission management setup
mm.start_mission()
mm.log_event("Mission started", severity=st.Severity.Info)

# Simulation loop
exit_flag = False
while not exit_flag:
    # Wait for the next loop iteration
    time.sleep(1.0 / LoopFreqHz)

    ### Charging Logic ###
    for en in every_en:
        try:
            en_xy, _ = ET.GetCurrentXY(en)
            charging_xy = ET.GetChargingStationXY()

            for edge in edge_list:
                try:
                    en_from = power_assembly.GetParam(st.VarType.entityRef, ["#Assembly", "Edges", edge, "From"])
                    en_to = power_assembly.GetParam(st.VarType.entityRef, ["#Assembly", "Edges", edge, "To"])

                    # Check if charging station is connected to the entity
                    if en_from == charging_station and en_to == en:
                        distance_squared = (en_xy.x - charging_xy.x) ** 2 + (en_xy.y - charging_xy.y) ** 2
                        is_within_radius = distance_squared < CHARGING_RADIUS_M ** 2

                        # Activate or deactivate charging based on distance
                        power_assembly.SetParam(st.VarType.bool, ["#Assembly", "Edges", edge, "IsActive"], is_within_radius)
                except Exception as e:
                    st.OnScreenLogMessage(f"Error processing edge {edge} for entity {en.getName()}: {e}", "Competition Backend", st.Severity.Error)
        except Exception as e:
            st.OnScreenLogMessage(f"Error processing charging logic for entity {en.getName()}: {e}", "Competition Backend", st.Severity.Error)

    ### Simulation End Condition ###
    end_condition = True
    any_robot_reached_crash_site = False

    # Check if any robot has reached the crash site
    for en in every_en:
        try:
            target_found, target_xy, had_comms = ET.GetTargetScanStatus(en)
            if target_found:
                any_robot_reached_crash_site = True
                mm.log_event(f"{en.getName()} has reached the crash site.", severity=st.Severity.Info)
                break
        except Exception as e:
            st.OnScreenLogMessage(f"Error checking target status for entity {en.getName()}: {e}", "Competition Backend", st.Severity.Error)

    # Only end the simulation if a robot has reached the crash site
    if not any_robot_reached_crash_site:
        end_condition = False

    if end_condition:
        try:
            st.SimGlobals_SimClock_Freeze()
            st.OnScreenLogMessage("Simulation end conditions met; freezing simulation and recording results.", 
                                  "Competition Backend", st.Severity.Info)

            # Calculate and display the simulation duration
            sim_end_time: st.timestamp = st.SimGlobals_SimClock_GetTimeNow()
            sim_duration = sim_end_time.as_datetime() - sim_start_time.as_datetime()
            mm.log_event(f"Simulation completed in {sim_duration}.", severity=st.Severity.Info)

            # Log mission status update
            mm.update_mission_status("completed")
            mm.end_mission()
            
            exit_flag = True
        except Exception as e:
            st.OnScreenLogMessage(f"Error during simulation end: {e}", "Competition Backend", st.Severity.Error)
            mm.log_event(f"Simulation end error: {e}", severity=st.Severity.Error)

# Post-simulation alert loop for result display
try:
    while True:
        st.OnScreenAlert(f"Simulation complete; time elapsed: {sim_duration}", 
                         "Simulation Complete", st.Severity.Info)
        time.sleep(0.5)
except Exception as e:
    st.OnScreenLogMessage(f"Error in post-simulation display loop: {e}", "Competition Backend", st.Severity.Error)

# Exit simulation
try:
    st.leave_sim()
    mm.log_event("Exited simulation successfully.", severity=st.Severity.Info)
except Exception as e:
    st.OnScreenLogMessage(f"Error while exiting simulation: {e}", "Competition Backend", st.Severity.Error)
    mm.log_event(f"Exit simulation error: {e}", severity=st.Severity.Error)

