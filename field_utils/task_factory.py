"""
Task creation and mission generation logic.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from .models import (
    Environment,
    Mission,
    NavigationTask,
    InspectionTask,
    SimpleInspectionTask,
    UndockTask,
    DockTask,
    SleepTask,
    MissionTask,
)


@dataclass
class TaskConfig:
    """Configuration for a task type."""

    task_prefix: str
    item_suffix: str
    plugin: str
    task_class: type


TASK_CONFIGS: Dict[str, TaskConfig] = {
    "visual_inspection_thermal": TaskConfig(
        task_prefix="Inspect",
        item_suffix="VIT",
        plugin="visual_inspection_thermal_behavior_plugins",
        task_class=InspectionTask,
    ),
    "inspection_intelligence": TaskConfig(
        task_prefix="Inspect",
        item_suffix="II",
        plugin="inspection_intelligence_behavior_plugins",
        task_class=InspectionTask,
    ),
    "auditive_inspection_frequency": TaskConfig(
        task_prefix="Inspect",
        item_suffix="AudioFreq",
        plugin="auditive_inspection_frequency_behavior_plugins",
        task_class=InspectionTask,
    ),
    "visual_inspection_simple": TaskConfig(
        task_prefix="Inspect",
        item_suffix="VIS",
        plugin="visual_inspection_simple_behavior_plugins",
        task_class=SimpleInspectionTask,
    ),
    "auditive_inspection_simple": TaskConfig(
        task_prefix="Inspect",
        item_suffix="AudioS",
        plugin="auditive_inspection_simple_behavior_plugins",
        task_class=SimpleInspectionTask,
    ),
    "visual_inspection_video_recording": TaskConfig(
        task_prefix="Record",
        item_suffix="VSVR",
        plugin="visual_inspection_video_recording_behavior_plugins",
        task_class=SimpleInspectionTask,
    ),
    "navigation_goal": TaskConfig(
        task_prefix="Navigate to",
        item_suffix="NavGoal",
        plugin="navigation_behavior_plugins",
        task_class=NavigationTask,
    ),
}


def create_task_entry(task: Dict[str, Any], env: Environment) -> Optional[MissionTask]:
    """
    Convert a simple task specification into a full mission task.

    Args:
        task: Task specification with 'name', 'type', optional 'label', 'action', 'duration'
        env: Environment to validate object references

    Returns:
        MissionTask instance or None if task cannot be created
    """
    if "label" not in task:
        task["label"] = task["name"]

    task_type = task.get("type", "")

    if not task_type:
        env_obj = env.get_object(task["name"])
        if env_obj is None:
            print(f"Warning: Object '{task['name']}' not found in environment.")
            return None
        task_type = env_obj.type

    # Handle special system tasks
    if task_type == "undock":
        return UndockTask(name=task.get("label", "Undock"))

    if task_type == "dock":
        return DockTask(
            name=task.get("label", "Dock"),
            docking_station=task.get("docking_station", "Suggested")
        )

    if task_type == "sleep":
        return SleepTask(
            name=task.get("label", f"Sleep {task['name']}"),
            duration=task.get("duration", 5.0)
        )

    # Handle regular tasks with configuration
    if task_type not in TASK_CONFIGS:
        print(f"Cannot create task of type: {task_type}")
        return None

    config = TASK_CONFIGS[task_type]

    # Validate object exists in environment (with suffix fallback)
    object_name = task["name"]
    if not env.has_object(object_name):
        object_name_with_suffix = f"{task['name']}-{config.item_suffix}"
        if env.has_object(object_name_with_suffix):
            object_name = object_name_with_suffix
        else:
            print(f"Warning: Object '{task['name']}' not found in environment.")
            return None

    # Create the appropriate task
    task_name = f"{config.task_prefix} {task['label']}" if config.task_prefix else task["label"]
    action = task.get("action", "Inspect")

    if config.task_class == NavigationTask:
        return NavigationTask(
            name=task_name,
            navigation_goal=object_name,
            route_option="Along Waypoints"
        )
    elif config.task_class == InspectionTask:
        return InspectionTask(
            name=task_name,
            inspectable_item=object_name,
            plugin=config.plugin,
            action=action
        )
    elif config.task_class == SimpleInspectionTask:
        return SimpleInspectionTask(
            name=task_name,
            inspectable_item=object_name,
            plugin=config.plugin,
            action=action
        )
    else:
        print(f"Unknown task class: {config.task_class}")
        return None


def process_mission_generation(
    task_list_data: List[Dict[str, Any]],
    env: Environment,
    mission_name: str
) -> Mission:
    """
    Generate a complete mission from a list of simple task specifications.

    Args:
        task_list_data: List of task specifications
        env: Environment for validation
        mission_name: Name for the mission

    Returns:
        Mission object ready for serialization
    """
    mission_tasks: List[MissionTask] = []

    for task_spec in task_list_data:
        mission_task = create_task_entry(task_spec, env)
        if mission_task is None:
            continue
        mission_tasks.append(mission_task)

    # Link tasks sequentially
    for i in range(len(mission_tasks) - 1):
        mission_tasks[i].link_to(mission_tasks[i + 1])

    # Mark final task
    if mission_tasks:
        mission_tasks[-1].set_as_final()

    # Create mission
    initial_state = mission_tasks[0].name if mission_tasks else ""
    return Mission(name=mission_name, initial_state=initial_state, states=mission_tasks)
