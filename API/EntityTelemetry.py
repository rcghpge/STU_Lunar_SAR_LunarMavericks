import os, sys, time, datetime, traceback
import spaceteams as st
import numpy as np

import API.SurfaceMovement as SM
from API.STU_Common import XY, Command, CoordToXY

#TODO docstrings on all of these functions


def LatLonAltToXY(lla: st.PlanetUtils.LatLonAlt) -> XY:
    planet: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "Planet")
    radius = planet.GetParam(st.VarType.double, ["#Planet", "General", "Radius"]) * 1000.0
    return CoordToXY(st.PlanetUtils.Coord(lla, 0.0, radius))


def XYToLatLonAlt(en: st.Entity, xy: XY) -> st.PlanetUtils.LatLonAlt:
    return xy.toLLA()


def HasComms(en: st.Entity) -> bool:
    return en.GetParam(st.VarType.bool, "HasComms")


def GetMovementState(en: st.Entity) -> tuple[str, bool]:
    '''
    Get the movement state of the entity.
    Also returns whether the entity had comms.
    If the entity does not have comms, the function will return a default value.

    Movement states:
    Loiter      - The entity is stationary.
    LoiterUntil - (unused) The entity is stationary until a certain time.
    Ride        - (unused) The entity is embarked on another entity.
    StopRide    - (unused) The Entity is disembarking from another entity.
    Startup     - (unused) The entity is starting up.
    Moving      - The entity is moving to a destination.
    Reversing   - The entity is moving in reverse to a destination.
    Cooldown    - (unused) The entity is shutting down.
    '''
    mover = SM.SurfaceMover(en, st.GetSimEntity().GetParam(st.VarType.entityRef, "Planet"))
    has_comms = HasComms(en)
    if has_comms:
        return mover.GetMovementState(), has_comms
    else:
        return "", has_comms


def IsMoving(en: st.Entity) -> tuple[bool, bool]:
    '''
    Get whether the entity is currently moving.
    Also returns whether the entity had comms.
    If the entity does not have comms, the function will return a default value.
    '''
    mover = SM.SurfaceMover(en, st.GetSimEntity().GetParam(st.VarType.entityRef, "Planet"))
    has_comms = HasComms(en)
    if has_comms:
        return mover.IsMoving(), has_comms
    else:
        return False, has_comms


def GetCurrentXY(en: st.Entity) -> tuple[XY, bool]:
    '''
    Get the current XY coordinate of the entity.
    Also returns whether the entity had comms.
    If the entity does not have comms, the function will return a default value.
    '''
    mover = SM.SurfaceMover(en, st.GetSimEntity().GetParam(st.VarType.entityRef, "Planet"))
    has_comms = HasComms(en)
    if has_comms:
        current_coord = mover.GetCurrentCoord()
        return CoordToXY(current_coord), has_comms
    else:
        return XY(0, 0), has_comms


def GetMoveToXY(en: st.Entity) -> tuple[XY, bool]:
    '''
    Get the current move-to waypoint XY coordinate of the entity.
    Also returns whether the entity had comms.
    If the entity does not have comms, the function will return a default value.
    '''
    mover = SM.SurfaceMover(en, st.GetSimEntity().GetParam(st.VarType.entityRef, "Planet"))
    has_comms = HasComms(en)
    if has_comms:
        move_to_coord = mover.GetMoveToCoord()
        return CoordToXY(move_to_coord), has_comms
    else:
        return XY(0, 0), has_comms


def GetAzimuth(en: st.Entity) -> tuple[float, bool]:
    '''
    Get the current azimuth of the entity.
    Also returns whether the entity had comms.
    If the entity does not have comms, the function will return a default value.
    '''
    mover = SM.SurfaceMover(en, st.GetSimEntity().GetParam(st.VarType.entityRef, "Planet"))
    has_comms = HasComms(en)
    if has_comms:
        return mover.GetAzimuth(), has_comms
    else:
        return 0.0, has_comms

def GetLidarObstacles(en: st.Entity) -> tuple[list, list, bool]:
    '''
    Returns a list of relative vectors to obstacles and their radii.
    3rd element of the returned tuple is whether the entity has comms and thus whether the
    returned values are valid.
    Also returns whether the entity had comms.
    If the entity does not have comms, the function will return a default value.
    '''
    has_comms = HasComms(en)
    if has_comms:
        scanner_en : st.Entity = en.GetParam(st.VarType.entityRef, "Scanner")
        rel_vecs_and_radii = scanner_en.GetParamArray(st.VarType.doubleV4, "RelVecsAndRadii")
        rel_vecs = [np.asarray(rel_vec_and_radius[:3]) for rel_vec_and_radius in rel_vecs_and_radii]
        radii = [rel_vec_and_radius[3] for rel_vec_and_radius in rel_vecs_and_radii]
        return rel_vecs, radii, has_comms
    else:
        return [], [], has_comms

def GetTargetScanStatus(en: st.Entity) -> tuple[bool, XY, bool]:
    '''
    Returns whether a target has been found and the location of the found target.
    Also returns whether the entity had comms.
    If the entity does not have comms, the function will return a default value.
    '''
    has_comms = HasComms(en)
    if has_comms:
        scanner_en : st.Entity = en.GetParam(st.VarType.entityRef, "Scanner")
        found: bool = scanner_en.GetParam(st.VarType.bool, "TargetFound")
        loc = scanner_en.GetParam(st.VarType.doubleV3, "TargetLocation")
        xy = CoordToXY(st.PlanetUtils.Coord(loc, np.identity(3), 1737400))
        if not found:
            cam_scanner_en : st.Entity = en.GetParam(st.VarType.entityRef, "CamScanner")
            found: bool = cam_scanner_en.GetParam(st.VarType.bool, "TargetFound")
            loc = cam_scanner_en.GetParam(st.VarType.doubleV3, "TargetLocation")
            xy = CoordToXY(st.PlanetUtils.Coord(loc, np.identity(3), 1737400))
        return found, xy, has_comms
    else:
        return False, XY(0,0), has_comms
    
def GetStateOfCharge(en: st.Entity) -> tuple[float, bool]:
    '''
    Returns the 0-1 fraction of charge of the entity's battery.
    Also returns whether the entity had comms.
    If the entity does not have comms, the function will return a default value.
    '''
    has_comms = HasComms(en)
    if has_comms:
        battery_en : st.Entity = en.GetParam(st.VarType.entityRef, "Battery")
        current_energy_J = battery_en.GetParam(st.VarType.double, ["Resources", "currentPower"])
        max_energy_storage_J = battery_en.GetParam(st.VarType.double, ["Resources", "Maximum_Power_Storage"])
        return current_energy_J / max_energy_storage_J, has_comms
    else:
        return 0.0, has_comms
    
def GetChargingStationXY():
    '''
    Returns the XY coordinate of the charging station.
    Doesn't require comms.
    '''
    charging_station_en : st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "ChargingStation")
    mover = SM.SurfaceMover(charging_station_en, st.GetSimEntity().GetParam(st.VarType.entityRef, "Planet"))
    current_coord = mover.GetCurrentCoord()
    return CoordToXY(current_coord)