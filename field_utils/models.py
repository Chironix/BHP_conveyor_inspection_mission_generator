"""
Models of the ANYmal mission and environment configuration file elements.

This module defines the models for:
- Mission tasks (navigation, inspection, system tasks)
- Environment objects (navigation goals, inspection points, docking stations)
- Supporting structures (poses, transitions, etc.)

There is limited business logic in this module.
However, some of the business logic is captured in the methods surrounding transitions between
tasks.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


# ============================================================================
# Simple Data Structures
# ============================================================================

@dataclass
class Position:
    """3D position in map frame."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Orientation:
    """Quaternion orientation."""

    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Tolerance:
    """Position and rotation tolerances."""

    translation: float = 0.05
    rotation: float = 0.104719758033752  # ~6 degrees in radians


@dataclass
class Size:
    """2D size for inspection areas."""

    width: float = 0.1
    height: float = 0.8


@dataclass
class TemperatureRange:
    """Operating temperature range for thermal inspections."""

    min: float = -20.0
    max: float = 900.0


@dataclass
class Transition:
    """Task transition defining outcome-based flow control."""

    outcome: str
    transition: str
    transition_to_state: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        return asdict(self)


@dataclass
class Setting:
    """Task setting with name, type, and value."""

    name: str
    type: str
    value: Any

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        return asdict(self)


@dataclass
class ObjectRelation:
    """Relationship between two environment objects (e.g., goal belongs to zone)."""

    child: str
    parent: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        return asdict(self)


@dataclass
class Pose:
    """Complete pose with position and orientation."""

    position: Position = field(default_factory=Position)
    orientation: Orientation = field(default_factory=Orientation)

    def set_position(self, x: float, y: float, z: float) -> None:
        """Update position coordinates."""
        self.position.x = x
        self.position.y = y
        self.position.z = z

    def set_orientation(self, w: float, x: float, y: float, z: float) -> None:
        """Update orientation quaternion."""
        self.orientation.w = w
        self.orientation.x = x
        self.orientation.y = y
        self.orientation.z = z


class PoseStamped:
    """
    Encapsulates the nested structure used in ANYmal environment files.
    """

    def __init__(self):
        self.pose = Pose()
        self.tolerance: Optional[Tolerance] = None

    def set_position(self, x: float, y: float, z: float) -> None:
        """Set position coordinates."""
        self.pose.set_position(x, y, z)

    def set_orientation(self, w: float, x: float, y: float, z: float) -> None:
        """Set orientation quaternion."""
        self.pose.set_orientation(w, x, y, z)

    def set_translation_tolerance(self, tolerance: float) -> None:
        """Set position tolerance."""
        if self.tolerance is None:
            self.tolerance = Tolerance()
        self.tolerance.translation = tolerance

    def set_rotation_tolerance(self, tolerance: float) -> None:
        """Set rotation tolerance."""
        if self.tolerance is None:
            self.tolerance = Tolerance()
        self.tolerance.rotation = tolerance

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        result = {
            "header": {"frame_id": "map"},
            "pose": asdict(self.pose)
        }
        if self.tolerance is not None:
            result["tolerance"] = asdict(self.tolerance)
        return result


# ============================================================================
# Environment Config Objects
# ============================================================================

class EnvironmentObject(ABC):
    """
    Base class for all environment objects.

    All objects in the ANYmal environment have a name, label, type, and pose.
    Subclasses define specific object types with additional fields.

    - name:     Unique identifier
    - label:    Human-readable descriptor
    - type:     Descriptor of the inspectable object type, needed for mission runner
    - pose:     Position in the world
    """

    def __init__(self, name: str, label: str, obj_type: str):
        self.name = name
        self.label = label
        self.type = obj_type
        self.pose = PoseStamped()

    def set_position(self, x: float, y: float, z: float) -> None:
        """Set the object's position."""
        self.pose.set_position(x, y, z)

    def set_orientation(self, w: float, x: float, y: float, z: float) -> None:
        """Set the object's orientation."""
        self.pose.set_orientation(w, x, y, z)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        return {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "pose": self.pose.to_dict()
        }


class NavigationGoal(EnvironmentObject):
    """Navigation goal waypoint in the environment."""

    def __init__(self, name: str, label: Optional[str] = None):
        super().__init__(name, label or name, "navigation_goal")

    def set_translation_tolerance(self, tolerance: float) -> None:
        """Set position tolerance."""
        self.pose.set_translation_tolerance(tolerance)

    def set_rotation_tolerance(self, tolerance: float) -> None:
        """Set rotation tolerance."""
        self.pose.set_rotation_tolerance(tolerance)


class NavigationZone:
    """
    The Navigation Zone "special" object in the environment that relates to Navigation Goals
    """

    def __init__(self, name: str, label: Optional[str] = None):
        self.name = name
        self.label = label or name
        self.type = "navigation_zone"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        return {
            "name": self.name,
            "label": self.label,
            "type": self.type
        }


class DockingStation(EnvironmentObject):
    """Docking station for robot charging."""

    def __init__(self, name: str, label: Optional[str] = None):
        super().__init__(name, label or name, "docking_station")

    def set_translation_tolerance(self, tolerance: float) -> None:
        """Set position tolerance."""
        self.pose.set_translation_tolerance(tolerance)

    def set_rotation_tolerance(self, tolerance: float) -> None:
        """Set rotation tolerance."""
        self.pose.set_rotation_tolerance(tolerance)


class ThermalInspectionPoint(EnvironmentObject):
    """Thermal inspection point in the environment."""

    def __init__(self, name: str, label: Optional[str] = None):
        super().__init__(name, label or name, "visual_inspection_thermal")
        self.min_certainty = 0.6
        self.temperature_type = "Max"
        self.unit = "degreesC"
        self.normal_operating_range = TemperatureRange()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        base = super().to_dict()
        base.update({
            "min_certainty": self.min_certainty,
            "temperature_type": self.temperature_type,
            "unit": self.unit,
            "normal_operating_range": asdict(self.normal_operating_range)
        })
        return base


class VisualInspectionPoint(EnvironmentObject):
    """Visual inspection point in the environment."""

    def __init__(self, name: str, label: Optional[str] = None):
        super().__init__(name, label or name, "visual_inspection_simple")
        self.camera_type = "normal"
        self.size = Size()

    def set_size(self, width: float, height: float) -> None:
        """Set inspection area size."""
        self.size.width = width
        self.size.height = height

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        base = super().to_dict()
        base.update({
            "camera_type": self.camera_type,
            "size": asdict(self.size)
        })
        return base


# ============================================================================
# Mission Config Task Objects
# ============================================================================

class MissionTask(ABC):
    """
    Base class for all mission tasks.

    All tasks have a name, type, settings, and transitions.
    Subclasses define specific task types and their settings.
    """

    def __init__(self, name: str, task_type: str, settings: Optional[List[Setting]] = None):
        self.name = name
        self.type = task_type
        self.settings = settings or []
        self.transitions = self._create_default_transitions()

    @abstractmethod
    def _create_default_transitions(self) -> List[Transition]:
        """Create default transitions for this task type. Subclasses must implement."""
        pass

    def link_to(self, next_task: 'MissionTask') -> None:
        """Link this task to the next task in the sequence."""
        for transition in self.transitions:
            if transition.transition == "[next_task_name]":
                transition.transition = next_task.name

    def set_as_final(self) -> None:
        """Mark this as the final task in the mission."""
        for transition in self.transitions:
            if transition.transition == "[next_task_name]":
                transition.transition_to_state = False
                if transition.outcome in ["success", "normal"]:
                    transition.transition = "success"
                else:
                    transition.transition = "failure"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "settings": [s.to_dict() for s in self.settings],
            "transitions": [t.to_dict() for t in self.transitions]
        }


class UndockTask(MissionTask):
    """Undock from charging station task."""

    def __init__(self, name: str = "Undock"):
        super().__init__(name, "system_behavior_plugins::Walk", [])

    def _create_default_transitions(self) -> List[Transition]:
        return [
            Transition("failure", "failure", False),
            Transition("preemption", "preemption", False),
            Transition("success", "[next_task_name]", True),
        ]


class DockTask(MissionTask):
    """Dock to charging station task."""

    def __init__(self, name: str = "Dock", docking_station: str = "Suggested"):
        settings = [Setting("docking_station", "DockingStation", docking_station)]
        super().__init__(name, "docking_behavior_plugins::Dock", settings)

    def _create_default_transitions(self) -> List[Transition]:
        return [
            Transition("failure", "failure", False),
            Transition("preemption", "preemption", False),
            Transition("success", "success", False),
        ]


class SleepTask(MissionTask):
    """Sleep/wait task."""

    def __init__(self, name: str, duration: float = 5.0):
        settings = [Setting("duration", "double", duration)]
        super().__init__(name, "basic_behavior_plugins::Sleep", settings)

    def _create_default_transitions(self) -> List[Transition]:
        return [
            Transition("failure", "failure", False),
            Transition("preemption", "preemption", False),
            Transition("success", "[next_task_name]", True),
        ]


class NavigationTask(MissionTask):
    """Navigate to a goal waypoint task."""

    def __init__(self, name: str, navigation_goal: str, route_option: str = "Along Waypoints"):
        settings = [
            Setting("navigation_goal", "NavigationGoal", navigation_goal),
            Setting("route_option", "RouteOption", route_option),
        ]
        super().__init__(name, "navigation_behavior_plugins::ReactiveNavigation", settings)

    def _create_default_transitions(self) -> List[Transition]:
        return [
            Transition("failure", "[next_task_name]", True),
            Transition("preemption", "preemption", False),
            Transition("success", "[next_task_name]", True),
        ]


class InspectionTask(MissionTask):
    """
    Base class for inspection tasks with anomaly detection.

    Used for thermal and intelligent inspections.
    """

    def __init__(self, name: str, inspectable_item: str, plugin: str, action: str = "Inspect"):
        settings = [Setting("inspectable_item", "InspectableItem", inspectable_item)]
        super().__init__(name, f"{plugin}::{action}", settings)

    def _create_default_transitions(self) -> List[Transition]:
        return [
            Transition("anomaly", "[next_task_name]", True),
            Transition("failure", "[next_task_name]", True),
            Transition("normal", "[next_task_name]", True),
            Transition("preemption", "preemption", False),
        ]


class SimpleInspectionTask(MissionTask):
    """
    Simple inspection task without anomaly detection.

    Used for visual and auditive inspections.
    """

    def __init__(self, name: str, inspectable_item: str, plugin: str, action: str = "Inspect"):
        settings = [Setting("inspectable_item", "InspectableItem", inspectable_item)]
        super().__init__(name, f"{plugin}::{action}", settings)

    def _create_default_transitions(self) -> List[Transition]:
        return [
            Transition("failure", "[next_task_name]", True),
            Transition("success", "[next_task_name]", True),
            Transition("preemption", "preemption", False),
        ]


# ============================================================================
# Top-Level Container Classes
# ============================================================================

class Environment:
    """Complete environment with objects and their relationships."""

    def __init__(self):
        self.objects: List[Any] = []  # Can be EnvironmentObject or NavigationZone
        self.object_relations: List[ObjectRelation] = []

    def add_object(self, obj: Any) -> None:
        """Add an object to the environment."""
        self.objects.append(obj)

    def add_relation(self, child: str, parent: str) -> None:
        """Add a relationship between objects."""
        self.object_relations.append(ObjectRelation(child, parent))

    def has_object(self, name: str) -> bool:
        """Check if an object with the given name exists."""
        return any(obj.name == name for obj in self.objects)

    def get_object(self, name: str) -> Optional[Any]:
        """Get an object by name."""
        for obj in self.objects:
            if obj.name == name:
                return obj
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        return {
            "objects": [obj.to_dict() for obj in self.objects],
            "object_relations": [rel.to_dict() for rel in self.object_relations]
        }


@dataclass
class MissionSetting:
    """Mission-level setting."""

    name: str
    type: str
    value: Any

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        return asdict(self)


class Mission:
    """Complete mission with all tasks."""

    def __init__(self, name: str, initial_state: str, states: List[MissionTask]):
        self.name = name
        self.type = "state_machine::DynamicStateMachine"
        self.settings = [
            MissionSetting("default_initial_state", "DefaultInitialState", initial_state),
            MissionSetting("outcomes", "Outcomes", ["failure", "preemption", "success"]),
            MissionSetting("restart_on_execution", "bool", False),
            MissionSetting("states", "States", states),
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        settings_dict = []
        for setting in self.settings:
            if setting.name == "states":
                # Special handling for states - convert each task
                settings_dict.append({
                    "name": setting.name,
                    "type": setting.type,
                    "value": [task.to_dict() for task in setting.value]
                })
            else:
                settings_dict.append(setting.to_dict())

        return {
            "name": self.name,
            "type": self.type,
            "settings": settings_dict
        }
