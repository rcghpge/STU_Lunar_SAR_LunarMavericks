from API.STU_Common import *
import API.SurfaceMovement as SM
import API.EntityTelemetry as ET
import datetime

class MissionManager:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.status = "initialized"
        self.event_log = []
        self.entity_states = {}
        self.resources = {}

    def start_mission(self):
        """Starts the mission and records the start time."""
        self.start_time = datetime.datetime.now()
        self.status = "in progress"
        self.log_event("Mission started at " + str(self.start_time), severity=st.Severity.Info)

    def end_mission(self):
        """Ends the mission and records the end time."""
        self.end_time = datetime.datetime.now()
        self.status = "completed"
        duration = self.end_time - self.start_time if self.start_time else "N/A"
        self.log_event(f"Mission completed at {self.end_time} with duration {duration}", severity=st.Severity.Info)

    def log_event(self, message, severity=st.Severity.Info):
        """Logs an event with the given severity."""
        timestamp = datetime.datetime.now()
        event_entry = {"timestamp": timestamp, "message": message, "severity": severity}
        self.event_log.append(event_entry)
        st.OnScreenLogMessage(f"{timestamp}: {message}", "Mission Manager", severity)

    def update_mission_status(self, new_status):
        """Updates the mission status and logs the change."""
        old_status = self.status
        self.status = new_status
        self.log_event(f"Mission status updated from '{old_status}' to '{new_status}'", severity=st.Severity.Info)

    def track_entity_state(self, entity, state_key, state_value):
        """Tracks a specific state for an entity (e.g., location, battery level)."""
        if entity not in self.entity_states:
            self.entity_states[entity] = {}
        self.entity_states[entity][state_key] = state_value
        self.log_event(f"{entity.getName()}: {state_key} updated to {state_value}", severity=st.Severity.Debug)

    def monitor_resources(self, resource_name, amount):
        """Tracks resources like battery or fuel levels."""
        self.resources[resource_name] = amount
        self.log_event(f"Resource '{resource_name}' level set to {amount}", severity=st.Severity.Debug)

    def check_resource_levels(self, resource_name, threshold):
        """Checks if a resource is below a certain threshold and logs a warning."""
        if self.resources.get(resource_name, float('inf')) < threshold:
            self.log_event(f"Warning: Resource '{resource_name}' below threshold ({threshold})", severity=st.Severity.Warning)

    def entity_reached_target(self, entity):
        """Marks an entity as having reached its target."""
        self.track_entity_state(entity, "reached_target", True)
        self.log_event(f"{entity.getName()} has reached its target.", severity=st.Severity.Info)

    def mission_summary(self):
        """Generates a summary of the mission with key statistics and events."""
        duration = self.end_time - self.start_time if self.end_time and self.start_time else "N/A"
        summary = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": duration,
            "status": self.status,
            "events": self.event_log,
            "entity_states": self.entity_states,
            "resources": self.resources
        }
        self.log_event("Mission Summary Generated", severity=st.Severity.Info)
        return summary

    def OnCommandComplete(self, entity, command, callback=None):
        """Handles the completion of a command for a given entity."""
        self.log_event(f"{entity.getName()} completed command: {command}", severity=st.Severity.Info)

        # Execute callback if provided
        if callback:
            callback()

        # Update the entity state upon command completion, e.g., check if target is reached.
        if command == "MoveToTarget":
            self.entity_reached_target(entity)

    def OnCommandFail(self, entity, command, callback=None):
        """Handles the failure of a command for a given entity."""
        self.log_event(f"{entity.getName()} failed to execute command: {command}", severity=st.Severity.Warning)

        # Execute callback if provided
        if callback:
            callback()
