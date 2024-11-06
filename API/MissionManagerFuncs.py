import os, sys, time, datetime, traceback
import spaceteams as st
import numpy as np

from API.STU_Common import Command, _commandID_Str

class MissionManager:
    def __init__(self):#, en: st.Entity, planet: st.Entity):
        self.fail_reactions = dict()
        self.complete_reactions = dict()
        # self.en = en
        # self.planet = planet
        # self.pcpf: st.Frame = planet.GetBodyFixedFrame()
        # # Radius in km, converted to m
        # self.radius = planet.GetParam(st.VarType.double, ["#Planet", "General", "Radius"]) * 1000.0
    
    #TODO see if there are more things to do to make this a static func
    #TODO param key validation happens on ST Events; should move command name somewhere
    # else or sanitize it before passing into DispatchEvent
    
        
    def SendCommand(self, en : st.Entity, command_type : str, command : Command) -> bool:
        ''' 
        Sends a command to an entity.

        The payload can be used to send additional information about the command.

        Returns whether command sent successfully; will need to call this function again if
        the subject entity is not in comms.
        Use EnHasComms() to check if entity is in comms.
        '''
        commandID = _commandID_Str(en, command_type)
        command.payload.SetParam(st.VarType.string, ["#meta", "command_id"], commandID)
        command.payload.SetParam(st.VarType.string, ["#meta", "command_type"], command_type)
        if(self.EnHasComms(en)):
            st.SimGlobals_DispatchEvent(commandID, command.payload)
            return True
        else:
            return False
    

    def _handleCommandComplete(self, payload : st.ParamMap, timestamp : st.timestamp):
        '''
        Internal function; do not use.
        '''
        commandID = payload.GetParam(st.VarType.string, ["#meta", "command_id"])
        if commandID in self.complete_reactions:
            self.complete_reactions[commandID](payload)
        else:
            st.OnScreenLogMessage("Command completion reaction not found for command ID: " + commandID, 
                                  "Mission Manager", st.Severity.Warning)

    def OnCommandComplete(self, en : st.Entity, command_type : str, reaction ):
        '''
        Registers a reaction to a command completion.
        '''
        commandID = _commandID_Str(en, command_type)
        self.complete_reactions[commandID] = reaction
        st.SimGlobals_AddEventListener(commandID + "_Complete", self._handleCommandComplete)
    

    def _handleCommandFail(self, payload : st.ParamMap, timestamp : st.timestamp):
        '''
        Internal function; do not use.
        '''
        commandID = payload.GetParam(st.VarType.string, ["#meta", "command_id"])
        if commandID in self.fail_reactions:
            self.fail_reactions[commandID](payload)
        else:
            st.OnScreenLogMessage("Command failure reaction not found for command ID: " + commandID, 
                                  "Mission Manager", st.Severity.Warning)
    

    def OnCommandFail(self, en : st.Entity, command_type : str, reaction ):
        '''
        Registers a reaction to a command failure.
        '''
        commandID = _commandID_Str(en, command_type)
        self.fail_reactions[commandID] = reaction
        st.SimGlobals_AddEventListener(commandID + "_Fail", self._handleCommandFail)

    def EnHasComms(self, en: st.Entity) -> bool:
        '''
        Returns whether the entity is in comms.
        '''
        return en.GetParam(st.VarType.bool, "HasComms")