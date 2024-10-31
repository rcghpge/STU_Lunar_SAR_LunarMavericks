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

entities = st.GetThisSystem().GetParamArray(st.VarType.entityRef, "Entities")
LTV1: st.Entity = entities[0]
LTV2: st.Entity = entities[1]

# Get planet
planet: st.Entity = st.GetThisSystem().GetParam(st.VarType.entityRef, "Planet")

# Set up "mover" objects for all entities
mover_LTV1 = SM.SurfaceMover(LTV1, planet)
mover_LTV2 = SM.SurfaceMover(LTV2, planet)

#######################
##  Simulation Loop  ##
#######################

exit_flag = False
while not exit_flag:
    LoopFreqHz = st.GetThisSystem().GetParam(st.VarType.double, "LoopFreqHz")
    time.sleep(1.0 / LoopFreqHz)

    
    # Check whether the challenge end condition has been met
    # (For initial submission: Any robot reaches the crash site)
    # (For full submission: LTV with enough resources has reached the crash site)

    end_condition = True

    #TODO implementation
    any_robot_reached_crash_site = False

    target_found, target_xy, had_comms = ET.GetTargetScanStatus(LTV1)
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
