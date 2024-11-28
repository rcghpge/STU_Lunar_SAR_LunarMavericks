import os, sys, time, datetime, traceback
import spaceteams as st
import numpy as np

import API.SurfaceMovement as SM


class Command:
    def __init__(self, _type: str, _en: st.Entity):
        self.payload = st.ParamMap()
        self.en = _en
        self.command_type = _type
        self.command_id = _commandID_Str(self.en, _type)
        self.payload.AddParam(st.VarType.string, ["#meta", "command_type"], self.command_type)
        self.payload.AddParam(st.VarType.string, ["#meta", "command_id"], self.command_id)


class XY:
    def __init__(self, _x, _y):
        self.x = _x
        self.y = _y
        originEn: st.Entity = st.GetSimEntity().GetParam(st.VarType.entityRef, "LocalCoordinateOrigin")
        self.originSM = SM.SurfaceMover(originEn, st.GetSimEntity().GetParam(st.VarType.entityRef, "Planet"))
        self.originCoord: st.PlanetUtils.Coord = self.originSM.GetCurrentCoord()
        self.originLoc = self.originCoord.getLoc()
        self.originRot = self.originCoord.getRot()
        self.originNWU: st.PlanetUtils.NorthWestUp = self.originCoord.getNWU()
    
    def toCoord(self) -> st.PlanetUtils.Coord:
        loc = self.originLoc + self.originNWU.north() * self.x + self.originNWU.west() * self.y
        rot = self.originRot
        return st.PlanetUtils.Coord(loc, rot, self.originSM.radius)
    
    def toLLA(self) -> st.PlanetUtils.LatLonAlt:
        loc = self.originLoc + self.originNWU.north() * self.x + self.originNWU.west() * self.y
        return st.PlanetUtils.PCPF_to_LLA(loc, self.originSM.radius)


def CoordToXY(_coord: st.PlanetUtils.Coord) -> XY:
    xy = XY(0, 0)
    coord_offset = _coord.getLoc() - xy.originLoc
    xy.x = np.dot(coord_offset, xy.originNWU.north())
    xy.y = np.dot(coord_offset, xy.originNWU.west())
    return xy


def _commandID_Str(en : st.Entity, cmd_type : str):
    commandString = f"MM_Cmd_{en.getName()}_{cmd_type}"
    return commandString



def Command_MoveToCoord(en: st.Entity, xy: XY, task_id: str):
    '''
    Create a MoveToCoord command for an entity to move to a specified XY coordinate.
    For compatibility with the task graph, this move command also needs a task ID which
    uniquely identifies this command as a task.
    '''
    cmd = Command("MoveToCoord", en)
    cmd.payload.AddParam(st.VarType.entityRef, ["#meta", "Entity"], en)
    cmd.payload.AddParam(st.VarType.string, "TaskID", task_id)

    coord = xy.toCoord()
    cmd.payload.AddParam(st.VarType.doubleV3, "Loc", coord.getLoc())
    return cmd

def Command_RotateToAzimuth(en: st.Entity, azimuth: float, task_id: str):
    cmd = Command("RotateToAzimuth", en)
    cmd.payload.AddParam(st.VarType.string, "TaskID", task_id)
    cmd.payload.AddParam(st.VarType.double, "Azimuth", -azimuth)
    return cmd

def Command_CameraPan(en: st.Entity, azimuth_deg: float, elevation_deg: float, task_id: str):
    cmd = Command("CameraPan", en)
    cmd.payload.AddParam(st.VarType.string, "TaskID", task_id)
    cmd.payload.AddParam(st.VarType.double, "Azimuth", azimuth_deg)
    cmd.payload.AddParam(st.VarType.double, "Elevation", elevation_deg)
    return cmd

def Command_CaptureImage(en: st.Entity, exposure: float, task_id: str):
    cmd = Command("CaptureImage", en)
    cmd.payload.AddParam(st.VarType.string, "TaskID", task_id)
    cmd.payload.AddParam(st.VarType.double, "Exposure", exposure)
    return cmd