import os, sys, time, datetime, traceback
import spaceteams as st
import numpy as np

from API.STU_Common import Command, _commandID_Str


class EntityBehavior:
    def __init__(self, en: st.Entity) -> None:
        self.en = en
        self.scanner: st.Entity = en.GetParam(st.VarType.entityRef, "Scanner")
        self.battery: st.Entity = en.GetParam(st.VarType.entityRef, "Battery")
        self.camera: st.Entity = en.GetParam(st.VarType.entityRef, "Camera")
        self.command_reactions = dict()
        self.camera_capture_reaction = None
        self.active_commands = dict()
    

    def _handleCommandReceived(self, payload: st.ParamMap, timestamp: st.timestamp):
        commandType = payload.GetParam(st.VarType.string, ["#meta", "command_type"])
        commandID = payload.GetParam(st.VarType.string, ["#meta", "command_id"])
        command = Command(commandType, self.en)
        command.payload = payload

        if commandType in self.active_commands:
            st.OnScreenLogMessage(
                f"Entity {self.en.getName()} received a \"{commandType}\" command, but already has an active command of this type; ignoring the new command.", 
                "Entity Behavior", st.Severity.Error
            )
            return

        self.active_commands[commandType] = command
        self.command_reactions[commandType](command)


    def HasComms(self) -> bool:
        return self.en.GetParam(st.VarType.bool, "HasComms")
    

    def OnCommandReceived(self, command_type: str, reaction) -> None:
        self.command_reactions[command_type] = reaction
        commandID = _commandID_Str(self.en, command_type)
        st.SimGlobals_AddEventListener(commandID, self._handleCommandReceived)
    

    def CompleteCommand(self, command_type: str, payload: st.ParamMap) -> bool:
        commandID = _commandID_Str(self.en, command_type)
        payload.AddOrSetParam(st.VarType.string, ["#meta", "command_id"], commandID)
        payload.AddOrSetParam(st.VarType.string, ["#meta", "command_type"], command_type)
        orig_command: Command = self.active_commands[command_type]
        
        payload.AddParam(st.VarType.int32, ["Orig_Cmd", "_Dummy"], 0)
        payload.DeleteParam(["Orig_Cmd", "_Dummy"])

        orig_cmd_map = payload.GetParamMap("Orig_Cmd")
        orig_cmd_map.AddCopiesOfAllParamsFrom(orig_command.payload)
        
        if self.HasComms():
            del self.active_commands[command_type]
            st.SimGlobals_DispatchEvent(commandID + "_Complete", payload)
            return True
        else:
            return False
    

    def FailCommand(self, command_type: str, payload: st.ParamMap) -> bool:
        commandID = _commandID_Str(self.en, command_type)
        payload.AddOrSetParam(st.VarType.string, ["#meta", "command_id"], commandID)
        payload.AddOrSetParam(st.VarType.string, ["#meta", "command_type"], command_type)
        orig_command: Command = self.active_commands[command_type]
        
        payload.AddParam(st.VarType.int32, ["Orig_Cmd", "_Dummy"], 0)
        payload.DeleteParam(["Orig_Cmd", "_Dummy"])

        orig_cmd_map = payload.GetParamMap("Orig_Cmd")
        orig_cmd_map.AddCopiesOfAllParamsFrom(orig_command.payload)
        
        if self.HasComms():
            del self.active_commands[command_type]
            st.SimGlobals_DispatchEvent(commandID + "_Fail", payload)
            return True
        else:
            return False
    

    def ActiveCommands(self) -> dict:
        return self.active_commands
    

    def CameraPan(self, azimuth_deg: float, elevation_deg: float):
        camera_en: st.Entity = self.en.GetParam(st.VarType.entityRef, "Camera")
        rotation_matrix = np.array([
            [np.cos(np.radians(azimuth_deg)), -np.sin(np.radians(azimuth_deg)), 0],
            [np.sin(np.radians(azimuth_deg)), np.cos(np.radians(azimuth_deg)), 0],
            [0, 0, 1]
        ])
        camera_en.setRotation_DCM(rotation_matrix, self.en.GetBodyFixedFrame())
    

    def CameraCapture(self, exposure: float) -> int:
        properties = st.CaptureImageProperties()
        properties.EV = exposure
        properties.ResolutionX = 512
        properties.ResolutionY = 512
        properties.FOV = 90
        return st.CaptureImage(self.camera, properties)


    def _handleCameraCaptureDone(self, payload: st.ParamMap, timestamp: st.timestamp):
        captureID = payload.GetParamArray(st.VarType.int32, "CaptureID")
        pixelsR = payload.GetParamArray(st.VarType.uint8, "PixelsR")
        pixelsG = payload.GetParamArray(st.VarType.uint8, "PixelsG")
        pixelsB = payload.GetParamArray(st.VarType.uint8, "PixelsB")
        
        image_data = {
            "CaptureID": captureID,
            "RedChannel": pixelsR,
            "GreenChannel": pixelsG,
            "BlueChannel": pixelsB
        }

        if self.camera_capture_reaction:
            self.camera_capture_reaction(image_data)
