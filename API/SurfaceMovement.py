import os, sys, time, datetime, traceback
import spaceteams as st
import numpy as np


class SurfaceMover:
    def __init__(self, en: st.Entity, planet: st.Entity):
        self.en = en
        self.planet = planet
        self.pcpf: st.Frame = planet.GetBodyFixedFrame()
        # Radius in km, converted to m
        self.radius = planet.GetParam(st.VarType.double, ["#Planet", "General", "Radius"]) * 1000.0
    
    def GetMovementState(self) -> str:
        return st.SurfaceMove.GetMovementState(self.en)
    
    def IsMoving(self) -> bool:
        return st.SurfaceMove.IsMoving(self.en)
    
    def GetCurrentCoord(self) -> st.PlanetUtils.Coord:
        return st.SurfaceMove.GetCurrentCoord(self.en, self.pcpf, self.radius)
    
    def GetMoveToCoord(self) -> st.PlanetUtils.Coord:
        return st.SurfaceMove.GetMoveToCoord(self.en, self.pcpf, self.radius)
    
    def GetAzimuth(self) -> float:
        return st.SurfaceMove.GetAzimuth(self.en, self.pcpf, self.radius)
    
    def TurnToAzimuth(self, azimuth: float):
        return st.SurfaceMove.TurnToAzimuth(self.en, azimuth, self.pcpf, self.radius)
    
    def TurnAndMoveToCoord(self, coord: st.PlanetUtils.Coord):
        return st.SurfaceMove.TurnAndMoveToCoord(self.en, coord, self.pcpf, self.radius)
    
    def TurnAndReverseToCoord(self, coord: st.PlanetUtils.Coord):
        return st.SurfaceMove.TurnAndReverseToCoord(self.en, coord, self.pcpf, self.radius)

    def OnMoveComplete(self, reaction):
        st.SurfaceMove.OnMoveComplete(self.en, reaction)
