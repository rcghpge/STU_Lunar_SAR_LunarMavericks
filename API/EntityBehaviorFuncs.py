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
        #TODO may shift this to params so we can read the active commands from the 
        #   mission manager through entity telemetry
        self.active_commands = dict()
    

    def _handleCommandReceived(self, payload : st.ParamMap, timestamp : st.timestamp):
        '''
        Internal function; do not use.
        Called when a command is received.
        '''
        commandType = payload.GetParam(st.VarType.string, ["#meta", "command_type"])
        commandID = payload.GetParam(st.VarType.string, ["#meta", "command_id"])
        # st.OnScreenLogMessage("Active commands (after addition): " + str(self.ActiveCommands()), 
        #                       "Entity Behavior", st.Severity.Info)
        command = Command(commandType, self.en)
        command.payload = payload
        # If the command is already active, log an error and return
        if commandType in self.active_commands:
            st.OnScreenLogMessage("Entity "+ self.en.getName() + "Received a \"" + commandType + 
                                  "\" command, but already has an active command of this type; ignoring the new command.", 
                                  "Entity Behavior", st.Severity.Error)
            return
        # Store the command locally
        self.active_commands[commandType] = command
        # Run the reaction for this command
        self.command_reactions[commandType](command)

    def HasComms(self) -> bool:
        '''
        Whether this entity can communicate with the mission manager.
        '''
        return self.en.GetParam(st.VarType.bool, "HasComms")
    

    def OnCommandReceived(self, command_type : str, reaction) -> None:
        '''
        Registers a reaction to a command received by this entity.
        '''
        self.command_reactions[command_type] = reaction
        commandID = _commandID_Str(self.en, command_type)
        st.SimGlobals_AddEventListener(commandID, self._handleCommandReceived)
    

    #TODO may refactor to use Command object to identify command instead of
    # command name str, which would need to be extracted from somewhere?

    def CompleteCommand(self, command_type : str, payload: st.ParamMap) -> bool:
        ''' 
        Tells the mission manager that the command has been completed.

        The payload can be used to send additional information about the completion.

        Returns whether command-update sent successfully; will need to call this function again if not in comms.
        Use HasComms() to check if entity is in comms.
        '''
        commandID = _commandID_Str(self.en, command_type)
        payload.AddOrSetParam(st.VarType.string, ["#meta", "command_id"], commandID)
        payload.AddOrSetParam(st.VarType.string, ["#meta", "command_type"], command_type)
        # Get original command for usage in completion event
        orig_command : Command = self.active_commands[command_type]
        # Ensure a map exists at the "Orig_Cmd" key
        payload.AddParam(st.VarType.int32, ["Orig_Cmd", "_Dummy"], 0)
        payload.DeleteParam(["Orig_Cmd", "_Dummy"])
        # Put original command params into sub-map of payload
        orig_cmd_map = payload.GetParamMap("Orig_Cmd")
        orig_cmd_map.AddCopiesOfAllParamsFrom(orig_command.payload)
        # st.OnScreenLogMessage("Attempting to delete command '" + commandID + "' from list " + str(self.ActiveCommands()), 
        #                       "Entity Behavior", st.Severity.Info)
        if(self.HasComms()):
            del self.active_commands[command_type]
            st.SimGlobals_DispatchEvent(commandID + "_Complete", payload)
            return True
        else:   
            return False
    

    def FailCommand(self, command_type : str, payload: st.ParamMap) -> bool:
        ''' 
        Tells the mission manager that the command cannot be completed and has failed.

        The payload can be used to send additional information about the failure.

        Returns whether command-update sent successfully; will need to call this function again if not in comms
        Use HasComms() to check if entity is in comms.
        '''
        commandID = _commandID_Str(self.en, command_type)
        payload.AddOrSetParam(st.VarType.string, ["#meta", "command_id"], commandID)
        payload.AddOrSetParam(st.VarType.string, ["#meta", "command_type"], command_type)
        # Get original command for usage in completion event
        orig_command : Command = self.active_commands[command_type]
        # Ensure a map exists at the "Orig_Cmd" key
        payload.AddParam(st.VarType.int32, ["Orig_Cmd", "_Dummy"], 0)
        payload.DeleteParam(["Orig_Cmd", "_Dummy"])
        # Put original command params into sub-map of payload
        orig_cmd_map = payload.GetParamMap("Orig_Cmd")
        orig_cmd_map.AddCopiesOfAllParamsFrom(orig_command.payload)
        # st.OnScreenLogMessage("Attempting to delete command '" + commandID + "' from list " + str(self.ActiveCommands()), 
        #                       "Entity Behavior", st.Severity.Info)
        if(self.HasComms()):
            del self.active_commands[command_type]
            st.SimGlobals_DispatchEvent(commandID + "_Fail", payload)
            return True
        else:   
            return False
    

    def ActiveCommands(self) -> dict:
        '''
        Returns a dictionary of active commands.
        Key values are command types and values are Command objects.
        '''
        return self.active_commands
    
    def CameraPan(self, azimuth_deg: float, elevation_deg: float):
        '''
        Pan the entity's camera to the specified azimuth and elevation.
        '''
        #TODO construct 3d relative rotation from az and el
        # camera_en : st.Entity = self.en.GetParam(st.VarType.entityRef, "Camera")
        # camera_en.setRotation_DCM(np.identity(3), self.en.GetBodyFixedFrame()) #TODO
        pass

    def CameraCapture(self, exposure : float) -> int:
        '''
        Capture an image from the entity's camera.

        Use st.OnImageReceived(capture_id, .....) to register a reaction to the image capture right after calling this function.
        '''
        properties = st.CaptureImageProperties()
        properties.EV = exposure
        #TODO from camera en params
        properties.ResolutionX = 512
        properties.ResolutionY = 512
        properties.FOV = 90
        # leaving captureID blank so it randomizes
        return st.CaptureImage(self.camera, properties)

    def _handleCameraCaptureDone(self, payload : st.ParamMap, timestamp : st.timestamp):
        '''
        Internal function; do not use.
        Called when an image capture is done.
        '''
        #TODO correct for the actual image data
        captureID = payload.GetParamArray(st.VarType.int32, "CaptureID")
        pixelsR = payload.GetParamArray(st.VarType.uint8, "PixelsR")
        pixelsG = payload.GetParamArray(st.VarType.uint8, "PixelsG")
        pixelsB = payload.GetParamArray(st.VarType.uint8, "PixelsB")
        