import os, sys, time, datetime, traceback
import spaceteams as st
import numpy as np

class SurfaceMover:
    def __init__(self, en: st.Entity, planet: st.Entity):
        """
        Initializes a SurfaceMover for an entity on a specified planet.
        
        :param en: The entity to be moved.
        :param planet: The planet entity, providing the reference frame and radius.
        """
        self.en = en
        self.planet = planet
        self.pcpf: st.Frame = planet.GetBodyFixedFrame()
        # Radius in meters (converting from km)
        self.radius = planet.GetParam(st.VarType.double, ["#Planet", "General", "Radius"]) * 1000.0

    def GetMovementState(self) -> str:
        """Returns the current movement state of the entity (e.g., moving, stopped)."""
        return st.SurfaceMove.GetMovementState(self.en)

    def IsMoving(self) -> bool:
        """Returns True if the entity is currently moving; otherwise, False."""
        return st.SurfaceMove.IsMoving(self.en)

    def GetCurrentCoord(self) -> st.PlanetUtils.Coord:
        """Returns the current coordinate of the entity on the planet surface."""
        return st.SurfaceMove.GetCurrentCoord(self.en, self.pcpf, self.radius)

    def GetMoveToCoord(self) -> st.PlanetUtils.Coord:
        """Returns the coordinate that the entity is moving toward."""
        return st.SurfaceMove.GetMoveToCoord(self.en, self.pcpf, self.radius)

    def GetAzimuth(self) -> float:
        """Returns the current azimuth orientation of the entity in degrees."""
        return st.SurfaceMove.GetAzimuth(self.en, self.pcpf, self.radius)

    def TurnToAzimuth(self, azimuth: float):
        """
        Turns the entity to face a specific azimuth orientation.
        
        :param azimuth: The target azimuth in degrees.
        """
        result = st.SurfaceMove.TurnToAzimuth(self.en, azimuth, self.pcpf, self.radius)
        st.OnScreenLogMessage(f"{self.en.getName()} turning to azimuth {azimuth}°.", "SurfaceMover", st.Severity.Info)
        return result

    def TurnAndMoveToCoord(self, coord: st.PlanetUtils.Coord):
        """
        Turns the entity to face a target coordinate and moves it to that location.
        
        :param coord: The target coordinate on the planet surface.
        """
        result = st.SurfaceMove.TurnAndMoveToCoord(self.en, coord, self.pcpf, self.radius)
        st.OnScreenLogMessage(f"{self.en.getName()} moving to coordinate {coord}.", "SurfaceMover", st.Severity.Info)
        return result

    def TurnAndReverseToCoord(self, coord: st.PlanetUtils.Coord):
        """
        Turns the entity to face a target coordinate and reverses it to that location.
        
        :param coord: The target coordinate to reverse to on the planet surface.
        """
        result = st.SurfaceMove.TurnAndReverseToCoord(self.en, coord, self.pcpf, self.radius)
        st.OnScreenLogMessage(f"{self.en.getName()} reversing to coordinate {coord}.", "SurfaceMover", st.Severity.Info)
        return result

    def OnMoveComplete(self, reaction):
        """
        Sets a reaction function to trigger upon completion of a move command.
        
        :param reaction: A function to call when the move completes.
        """
        st.SurfaceMove.OnMoveComplete(self.en, reaction)
        st.OnScreenLogMessage(f"Move complete for {self.en.getName()}. Reaction set.", "SurfaceMover", st.Severity.Info)
