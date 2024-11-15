import os
import sys
import time
import datetime
import traceback
import spaceteams as st
import numpy as np

from API.STU_Common import Command, _commandID_Str

class MissionManager:
    def __init__(self):
        self.fail_reactions = dict()
        self.complete_reactions = dict()
    
    def SendCommand(self, en: st.Entity, command_type: str, command: Command) -> bool:
        """
        Sends a command to an entity.

        Args:
            en (st.Entity): The entity to send the command to.
            command_type (str): The type of command to send.
            command (Command): The command to send.

        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        try:
            # Assuming DispatchEvent is a method to send the command
            en.DispatchEvent(command_type, command)
            return True
        except Exception as e:
            print(f"Failed to send command: {e}")
            traceback.print_exc()
            return False

    def InitializeDataManager(self, data_manager_config: dict):
        """
        Initializes the DataManager with the given configuration.

        Args:
            data_manager_config (dict): The configuration for the DataManager.
        """
        try:
            # Example of accessing the configuration
            sim_entity = data_manager_config.get("SimEntity", {})
            time_config = sim_entity.get("Time", {})
            graphics_frame = sim_entity.get("GraphicsFrame", [])
            j2000_frame = sim_entity.get("J2000Frame", [])
            pawn = sim_entity.get("Pawn", [])
            power_assembly = sim_entity.get("PowerAssembly", [])
            charging_station = sim_entity.get("ChargingStation", [])
            habitat = sim_entity.get("Habitat", [])
            moon_inertial_frame = sim_entity.get("MoonInertialFrame", [])
            planet = sim_entity.get("Planet", [])
            target = sim_entity.get("Target", [])
            local_coordinate_origin = sim_entity.get("LocalCoordinateOrigin", [])
            location_options = sim_entity.get("LocationOptions", {})

            # Log the configuration for debugging
            print("DataManager Configuration:")
            print(f"Time: {time_config}")
            print(f"GraphicsFrame: {graphics_frame}")
            print(f"J2000Frame: {j2000_frame}")
            print(f"Pawn: {pawn}")
            print(f"PowerAssembly: {power_assembly}")
            print(f"ChargingStation: {charging_station}")
            print(f"Habitat: {habitat}")
            print(f"MoonInertialFrame: {moon_inertial_frame}")
            print(f"Planet: {planet}")
            print(f"Target: {target}")
            print(f"LocalCoordinateOrigin: {local_coordinate_origin}")
            print(f"LocationOptions: {location_options}")

            # Additional initialization logic here

        except Exception as e:
            print(f"Failed to initialize DataManager: {e}")
            traceback.print_exc()

# Example usage
if __name__ == "__main__":
    mm = MissionManager()
    # Example configuration
    data_manager_config = {
        "SimEntity": {
            "Time": {
                "UseCurrentTime": False,
                "Timescale": 1.0,
                "StartDateTAI": ["timestamp", "2026-06-05T19:00:00.000000Z"],
                "noEndDateTAI": ["timestamp", "2026-06-06T00:00:00.000000Z"]
            },
            "GraphicsFrame": ["EntityRef", "Moon"],
            "J2000Frame": ["EntityRef", "Moon_Inertial"],
            "Pawn": ["EntityRef", "Spectator1"],
            "PowerAssembly": ["EntityRef", "AdvRes_Power"],
            "ChargingStation": ["EntityRef", "ChargingStation"],
            "Habitat": ["EntityRef", "Habitat"],
            "MoonInertialFrame": ["EntityRef", "Moon_Inertial"],
            "Planet": ["EntityRef", "Moon"],
            "Target": ["EntityRef", "CrashedLunarLander"],
            "LocalCoordinateOrigin": ["EntityRef", "LocalCoordinateOrigin"],
            "LocationOptions": {
                "Location_ConnectingRidge": ["doubleV3", -12235.0, -11325.0, -1739279.5],
                "Location_LTV1": ["doubleV3", -12815.0, -12611.0, -1739202.0],
                "Location_LTV2": ["doubleV3", -12773.0, -12558.0, -1739221.0]
            }
        }
    }
    mm.InitializeDataManager(data_manager_config)