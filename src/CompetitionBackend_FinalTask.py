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

every_en : list[st.Entity] = st.GetThisSystem().GetParamArray(st.VarType.entityRef, "Entities")

# Get planet
planet: st.Entity = st.GetThisSystem().GetParam(st.VarType.entityRef, "Planet")

# Set up "mover" objects for all entities
# mover_LTV1 = SM.SurfaceMover(LTV1, planet)
# mover_LTV2 = SM.SurfaceMover(LTV2, planet)

charging_station: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "ChargingStation")
charging_station_generator: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "ChargingStationGenerator")
crash_site: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "Target")
power_assembly: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "PowerAssembly")

# Make both EVAs sit on LTV1:
EVA1: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "EVA1")
EVA2: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "EVA2")
LTV1: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "LTV1")
LTV1_BodyFrame: st.Frame = LTV1.GetBodyFixedFrame()

payload_EVA1 = st.ParamMap()
payload_EVA1.AddParam(st.VarType.string, "EVAEntity", EVA1.getName())
st.SimGlobals_DispatchEvent("StartSitting", payload_EVA1)
EVA1.SetParam(st.VarType.bool, "UpdateOnTick", False)
EVA1.setResidentFrame(LTV1_BodyFrame)

payload_EVA2 = st.ParamMap()
payload_EVA2.AddParam(st.VarType.string, "EVAEntity", EVA2.getName())
st.SimGlobals_DispatchEvent("StartSitting", payload_EVA2)
EVA2.SetParam(st.VarType.bool, "UpdateOnTick", False)
EVA2.setResidentFrame(LTV1_BodyFrame)

#######################
##  Simulation Loop  ##
#######################

CHARGING_RADIUS_M = 10.0
RESCUE_START_RADIUS_M = 20.0

exit_flag = False
while not exit_flag:
    LoopFreqHz = st.GetThisSystem().GetParam(st.VarType.double, "LoopFreqHz")
    time.sleep(1.0 / LoopFreqHz)

    ### Nominal sim code ###

    # EVA sit
    #NOTE should only have to do this once?
    EVA1.setLocation(np.array([-0.16, 0.5, 1.6]), LTV1_BodyFrame)
    EVA1.setRotation_DCM(np.identity(3), LTV1_BodyFrame)
    EVA1.setVelocity(np.zeros(3), LTV1_BodyFrame)
    EVA1.setAcceleration(np.zeros(3), LTV1_BodyFrame)
    EVA2.setLocation(np.array([-0.16, -0.5, 1.6]), LTV1_BodyFrame)
    EVA2.setRotation_DCM(np.identity(3), LTV1_BodyFrame)
    EVA2.setVelocity(np.zeros(3), LTV1_BodyFrame)
    EVA2.setAcceleration(np.zeros(3), LTV1_BodyFrame)


    # Charging
    # for en in every_en:
    if True:

        edge_list = ["ChargingStation_LTV1", 
                    "ChargingStation_LTV2", 
                    "ChargingStation_ScoutRover1", 
                    "ChargingStation_ScoutRover2", 
                    "ChargingStation_TruckRover",
                    "ChargingStation_ExcavatorRover",
                    "ChargingStation_SamplingRover",
                    # "Battery_LTV1", 
                    # "Battery_LTV2", 
                    # "ChargingStation_EVA1", 
                    # "ChargingStation_EVA2", 
                    # "Tank1_EVA1", 
                    # "Tank1_EVA2"
                    ]
        
        charging_xy = ET.GetChargingStationXY()
        
        for edge in edge_list:
            en_from : st.Entity = power_assembly.GetParam(st.VarType.entityRef, ["#Assembly", "Edges", edge, "From"])
            en_to : st.Entity = power_assembly.GetParam(st.VarType.entityRef, ["#Assembly", "Edges", edge, "To"])
            if en_from.getName() == charging_station_generator.getName():
                moving_en = en_to.GetParam(st.VarType.entityRef, "Owner")
                en_xy, _ = ET.GetCurrentXY(moving_en)
                # st.OnScreenLogMessage("DEBUG: evaluating " + en_from.getName() + " to " + en_to.getName(), "Competition Backend", st.Severity.Warning)
                edge_en : st.Entity = power_assembly.GetParam(st.VarType.entityRef, ["#Assembly", "Edges", edge, "Ref"])
                # Distance check
                if ((en_xy.x - charging_xy.x) ** 2 + (en_xy.y - charging_xy.y) ** 2) < CHARGING_RADIUS_M ** 2:
                    if not edge_en.GetParam(st.VarType.bool, "IsActive"):
                        st.OnScreenLogMessage("Attaching " + en_from.getName() + " to " + en_to.getName(), "Competition Backend", st.Severity.Info)
                    edge_en.SetParam(st.VarType.bool, "IsActive", True)
                else:
                    if edge_en.GetParam(st.VarType.bool, "IsActive"):
                        st.OnScreenLogMessage("Detaching " + en_from.getName() + " from " + en_to.getName(), "Competition Backend", st.Severity.Info)
                    edge_en.SetParam(st.VarType.bool, "IsActive", False)
                    #NOTE: discarded crew oxygen check

    ### Sim end condition checking ###
    # Check whether the challenge end condition has been met
    # (For initial submission: Any robot detects the crash site)
    # (For full submission: LTV with enough resources has reached the crash site)

    end_condition = True
    LTV1_is_at_crash_site = False

    # any_robot_reached_crash_site = False

    # for en in every_en:
    #     target_found, target_xy, had_comms = ET.GetTargetScanStatus(en)
    #     if(target_found):
    #         any_robot_reached_crash_site = True

    # if(not any_robot_reached_crash_site):
    #     end_condition = False

    # LTV1 proximity
    ltv1_mover = SM.SurfaceMover(LTV1, st.GetSimEntity().GetParam(st.VarType.entityRef, "Planet"))
    ltv1_xy = CoordToXY(ltv1_mover.GetCurrentCoord())
    #NOTE: this is only valid in the competition backend; you aren't supposed to directly sample the crash site location
    crash_mover = SM.SurfaceMover(crash_site, st.GetSimEntity().GetParam(st.VarType.entityRef, "Planet"))
    crash_xy = CoordToXY(crash_mover.GetCurrentCoord())

    if ((ltv1_xy.x - crash_xy.x) ** 2 + (ltv1_xy.y - crash_xy.y) ** 2) > RESCUE_START_RADIUS_M ** 2:
        end_condition = False
    else: # LTV1 is close enough to crash site
        LTV1_is_at_crash_site = True
    
    # LTV1 battery remaining
    battery_fraction = ET._GetStateOfCharge_Backend(LTV1)
    if battery_fraction < 0.5:
        end_condition = False
        if LTV1_is_at_crash_site:
            st.OnScreenLogMessage(f"{LTV1.getName()} is at crash site but battery state of charge is {battery_fraction*100.0}% which is less than 50%.", "Mission Manager", st.Severity.Warning)

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
