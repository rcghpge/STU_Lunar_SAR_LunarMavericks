import os, sys, time, datetime, traceback
import spaceteams as st
import numpy as np

from API.STU_Common import Command, _commandID_Str

def _rotation_matrix_z(angle_deg):
    """
    Returns the rotation matrix for a rotation about the Z-axis by the given angle in degrees.
    """
    angle_rad = np.radians(angle_deg)
    c = np.cos(angle_rad)
    s = np.sin(angle_rad)
    return np.array([[ c, -s, 0],
                    [ s,  c, 0],
                    [ 0,  0, 1]])

def _rotation_matrix_y(angle_deg):
    """
    Returns the rotation matrix for a rotation about the Y-axis by the given angle in degrees.
    """
    angle_rad = np.radians(angle_deg)
    c = np.cos(angle_rad)
    s = np.sin(angle_rad)
    return np.array([[ c,  0, s],
                    [ 0,  1, 0],
                    [-s,  0, c]])

def _calculate_passive_transformation_matrix(azimuth_deg, elevation_deg) -> np.ndarray[np.float64]:
    """
    Calculates the passive transformation matrix from the parent frame to the body frame,
    given parent-relative azimuth and elevation angles in degrees.
    """
    # Negative angles for passive transformation, but negative again because
    # az is a -z rotation and el is a -y rotation
    R_z = _rotation_matrix_z(azimuth_deg)
    R_y = _rotation_matrix_y(elevation_deg)
    
    # Compute the passive transformation matrix
    R_p2b = np.dot(R_y, R_z)
    return R_p2b


class EntityBehavior:
    def __init__(self, en: st.Entity) -> None:
        self.en = en
        self.objects: list[st.Entity] = []
        self.scanner: st.Entity = en.GetParam(st.VarType.entityRef, "Scanner")
        self.battery: st.Entity = en.GetParam(st.VarType.entityRef, "Battery")
        if(en.HasParam("Camera")):
            self.camera: st.Entity = en.GetParam(st.VarType.entityRef, "Camera")
        else:
            self.camera: st.Entity = None
            st.logger_warn(f"Entity {self.en.getName()} does not have a camera; camera functions will not work.")
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
        dcm = _calculate_passive_transformation_matrix(azimuth_deg, elevation_deg)
        self.camera.setRotation_DCM(dcm, self.en.GetBodyFixedFrame()) #TODO

    
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
        properties.FOV = self.camera.GetParam(st.VarType.double, "FOV")
        # leaving captureID blank so it randomizes
        return st.CaptureImage(self.camera, properties)
    
    
    def PickUpObject(self, param_list_name) -> int:
        if(self.en.getName() != "LTV1"):
            st.OnScreenLogMessage("Entity " + self.en.getName() + " is not the LTV1 with EVA crew onboard; cannot pick up objects.", 
                                  "Entity Behavior", st.Severity.Error)
            return -1
        objects: list[st.Entity] = st.GetSimEntity().GetParamArray(st.VarType.entityRef, param_list_name)
        distances: list[float] = []
        valid_objects: list[int] = []

        frame_pcpf: st.Frame = self.en.getResidentFrame()
        frame_en: st.Frame = self.en.GetBodyFixedFrame()
        en_loc = self.en.getLocation().WRT_ExprIn(frame_pcpf)
        
        for obj in objects:
            obj_loc = obj.getLocation().WRT_ExprIn(frame_pcpf)
            distance = np.linalg.norm(obj_loc - en_loc)
            if distance < 5.0:
                distances.append(distance)
                valid_objects.append(1)
            else:
                distances.append(1000000.0)
                valid_objects.append(0)
        if sum(valid_objects) > 0:
            min_idx = np.argmin(distances)
            obj = objects[min_idx]
            if obj.HasParam("UpdateOnTick"):
                obj.SetParam(st.VarType.bool, "UpdateOnTick", False)
            obj.setResidentFrame(frame_en)
            obj.setLocation(np.array([-1.0, 0.0, 1.6]), frame_en)
            obj.setRotation_DCM(np.identity(3), frame_en)
            obj.setVelocity(np.zeros(3), frame_en)
            obj.setAcceleration(np.zeros(3), frame_en)
            self.objects.append(obj)
            return 0
        else:
            return -1
    
    
    def PlaceDownObject(self) -> int:
        if (len(self.objects) > 0):
            obj: st.Entity = self.objects[0]
            if obj.HasParam("UpdateOnTick"):
                obj.SetParam(st.VarType.bool, "UpdateOnTick", True)
            frame_pcpf: st.Frame = self.en.getResidentFrame()
            en_loc = self.en.getLocation().WRT_ExprIn(frame_pcpf)
            obj.setResidentFrame(frame_pcpf)
            obj.setLocation(en_loc, frame_pcpf)
            obj.setVelocity(np.zeros(3), frame_pcpf)
            obj.setAcceleration(np.zeros(3), frame_pcpf)
            self.objects.clear()
            return 0
        else:
            return -1

    
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
        