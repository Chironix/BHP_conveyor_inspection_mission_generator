#!/usr/bin/env python3

import argparse
import yaml
import math
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from field_utils.yaml_dumper import AnyboticsYamlDumper
from field_utils.cli_helpers import env_info_parser
from field_utils.models import (
    Environment,
    NavigationGoal,
    NavigationZone,
    ThermalInspectionPoint,
    VisualInspectionPoint,
    DockingStation,
    Mission,
    NavigationTask,
    InspectionTask,
    SimpleInspectionTask,
    UndockTask,
    DockTask,
    SleepTask,
    MissionTask,
)


# ============================================================================
# Configuration
# ============================================================================

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


# ============================================================================
# Task Creation
# ============================================================================

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


# ============================================================================
# File I/O
# ============================================================================

def load_config(filename: str) -> List[Dict[str, Any]]:
    """Load configuration from YAML file."""
    with open(filename) as file:
        return yaml.safe_load(file)


def load_base_environment(filename: str) -> Environment:
    """Load base environment from YAML file into Environment object."""
    try:
        with open(filename) as file:
            data = yaml.safe_load(file)

        env = Environment()

        if "objects" in data:
            for obj_data in data["objects"]:
                if obj_data["type"] == "docking_station":
                    dock = DockingStation(obj_data["name"], obj_data.get("label"))
                    dock.set_position(
                        obj_data["pose"]["pose"]["position"]["x"],
                        obj_data["pose"]["pose"]["position"]["y"],
                        obj_data["pose"]["pose"]["position"]["z"]
                    )
                    dock.set_orientation(
                        obj_data["pose"]["pose"]["orientation"]["w"],
                        obj_data["pose"]["pose"]["orientation"]["x"],
                        obj_data["pose"]["pose"]["orientation"]["y"],
                        obj_data["pose"]["pose"]["orientation"]["z"]
                    )
                    dock.set_translation_tolerance(obj_data["pose"]["tolerance"]["translation"])
                    env.add_object(dock)
                elif obj_data["type"] == "navigation_goal":
                    nav = NavigationGoal(obj_data["name"], obj_data.get("label"))
                    nav.set_position(
                        obj_data["pose"]["pose"]["position"]["x"],
                        obj_data["pose"]["pose"]["position"]["y"],
                        obj_data["pose"]["pose"]["position"]["z"]
                    )
                    nav.set_orientation(
                        obj_data["pose"]["pose"]["orientation"]["w"],
                        obj_data["pose"]["pose"]["orientation"]["x"],
                        obj_data["pose"]["pose"]["orientation"]["y"],
                        obj_data["pose"]["pose"]["orientation"]["z"]
                    )
                    env.add_object(nav)

        if "object_relations" in data:
            for rel in data.get("object_relations", []):
                env.add_relation(rel["child"], rel["parent"])

        return env

    except FileNotFoundError:
        print(f"Base environment file '{filename}' not found. Starting with empty environment.")
        return Environment()


def save_environment(env: Environment, filename: str) -> None:
    """Save environment to YAML file."""
    with open(filename, "w") as file:
        file.write(
            yaml.dump(
                env.to_dict(),
                Dumper=AnyboticsYamlDumper,
                default_flow_style=False,
            )
        )


def save_task_list(task_list: List[Dict[str, Any]], filename: str) -> None:
    """Save task list to YAML file."""
    with open(filename, "w") as file:
        file.write(
            yaml.dump(
                task_list,
                Dumper=AnyboticsYamlDumper,
                default_flow_style=False,
            )
        )


def save_mission(mission: Mission, filename: str) -> None:
    """Save mission to YAML file."""
    with open(filename, "w") as file:
        file.write(
            yaml.dump(
                mission.to_dict(),
                Dumper=AnyboticsYamlDumper,
                default_flow_style=False,
            )
        )


# ============================================================================
# Geometry Calculations
# ============================================================================

def calculate_distance(start: List[float], end: List[float]) -> float:
    """Calculate Euclidean distance between two 3D points."""
    return math.sqrt(
        (start[0] - end[0]) ** 2 +
        (start[1] - end[1]) ** 2 +
        (start[2] - end[2]) ** 2
    )


def calculate_waypoint_position(
    start: List[float],
    end: List[float],
    spacing: float,
    index: int,
    distance: float
) -> List[float]:
    """Calculate position of a waypoint along a line segment."""
    ratio = index * spacing / distance if distance > 0 else 0
    return [
        start[0] + (end[0] - start[0]) * ratio,
        start[1] + (end[1] - start[1]) * ratio,
        start[2] + (end[2] - start[2]) * ratio,
    ]


# ============================================================================
# Environment Object Creation
# ============================================================================

def create_navigation_waypoint(
    name: str,
    position: List[float],
    entry: Dict[str, Any],
    env: Environment
) -> Tuple[NavigationGoal, NavigationZone]:
    """Create navigation goal and zone at the specified position."""
    nav_goal = NavigationGoal(f"{name}_NavGoal")
    nav_goal.set_position(*position)

    if "orientation" in entry:
        nav_goal.set_orientation(
            entry["orientation"]["w"],
            entry["orientation"]["x"],
            entry["orientation"]["y"],
            entry["orientation"]["z"]
        )

    if "translation_tolerance" in entry:
        nav_goal.set_translation_tolerance(entry["translation_tolerance"])

    env.add_object(nav_goal)

    nav_zone = NavigationZone(f"{name}_NavZone")
    env.add_object(nav_zone)
    env.add_relation(nav_goal.name, nav_zone.name)

    return nav_goal, nav_zone


def create_inspection_point(
    obj_name: str,
    position: List[float],
    inspection_config: Dict[str, Any],
    nav_zone: NavigationZone,
    env: Environment
) -> Optional[Dict[str, Any]]:
    """Create an inspection point and return its task specification."""
    inspection_type = inspection_config["type"]

    if inspection_type == "thermal_inspection":
        inspection = ThermalInspectionPoint(obj_name)
        inspection.set_position(*position)

        if "orientation" in inspection_config:
            inspection.set_orientation(
                inspection_config["orientation"]["w"],
                inspection_config["orientation"]["x"],
                inspection_config["orientation"]["y"],
                inspection_config["orientation"]["z"]
            )

        env.add_object(inspection)
        env.add_relation(nav_zone.name, inspection.name)

        return {
            "name": obj_name,
            "type": "visual_inspection_thermal",
            "action": "InspectFromHere"
        }

    elif inspection_type == "visual_inspection":
        inspection = VisualInspectionPoint(obj_name)
        inspection.set_position(*position)

        if "orientation" in inspection_config:
            inspection.set_orientation(
                inspection_config["orientation"]["w"],
                inspection_config["orientation"]["x"],
                inspection_config["orientation"]["y"],
                inspection_config["orientation"]["z"]
            )

        if "width" in inspection_config and "height" in inspection_config:
            inspection.set_size(
                inspection_config["width"],
                inspection_config["height"]
            )

        env.add_object(inspection)
        env.add_relation(nav_zone.name, inspection.name)

        return {
            "name": obj_name,
            "type": "visual_inspection_simple",
            "action": "InspectFromHere"
        }

    return None


# ============================================================================
# Segment Processing
# ============================================================================

def generate_waypoints_for_segment(
    entry: Dict[str, Any],
    env: Environment
) -> List[List[Dict[str, Any]]]:
    """
    Generate waypoints and environment objects for one segment.

    Returns:
        List of chunks, where each chunk contains tasks for one waypoint
        (navigation + inspections grouped together)
    """
    start = entry["start"]
    end = entry["end"]
    dist = calculate_distance(start, end)
    n = int(dist / entry["spacing"])

    mission_chunks = []

    for i in range(n + 1):
        current_chunk = []

        # Calculate waypoint position
        actual_nav_pos = calculate_waypoint_position(start, end, entry["spacing"], i, dist)

        # Create navigation waypoint
        waypoint_name = f"{entry['name']}{i}"
        nav_goal, nav_zone = create_navigation_waypoint(waypoint_name, actual_nav_pos, entry, env)

        # Add navigation task
        current_chunk.append({
            "name": nav_goal.name,
            "type": "navigation_goal"
        })

        # Create inspection points
        if "inspections" in entry:
            for inspection_entry in entry["inspections"]:
                inspection_pos = [
                    actual_nav_pos[0] + inspection_entry["offset"][0],
                    actual_nav_pos[1] + inspection_entry["offset"][1],
                    actual_nav_pos[2] + inspection_entry["offset"][2],
                ]

                # Determine object name based on inspection type
                if inspection_entry["type"] == "thermal_inspection":
                    obj_name = f"{waypoint_name}{inspection_entry['suffix']}VIT"
                elif inspection_entry["type"] == "visual_inspection":
                    obj_name = f"{waypoint_name}{inspection_entry['suffix']}VIS"
                else:
                    continue

                task_spec = create_inspection_point(
                    obj_name,
                    inspection_pos,
                    inspection_entry,
                    nav_zone,
                    env
                )

                if task_spec:
                    current_chunk.append(task_spec)

        mission_chunks.append(current_chunk)

    return mission_chunks


# ============================================================================
# Mission Generation
# ============================================================================

def generate_and_save_missions(
    segment_name: str,
    mission_chunks: List[List[Dict[str, Any]]],
    env: Environment,
    output_dir: str
) -> None:
    """Generate forward and reverse missions and save them to files."""
    # Forward mission: A -> B -> C (flatten chunks)
    forward_task_list = [task for chunk in mission_chunks for task in chunk]

    # Reverse mission: C -> B -> A (reverse chunks, keep internal order)
    reverse_task_list = [task for chunk in reversed(mission_chunks) for task in chunk]

    # Generate and save forward mission
    fwd_task_file = os.path.join(output_dir, f"{segment_name}_Forward_tasks.yaml")
    save_task_list(forward_task_list, fwd_task_file)

    mission_name_fwd = f"{segment_name}_Forward_Mission"
    final_mission_fwd = process_mission_generation(forward_task_list, env, mission_name_fwd)
    save_mission(final_mission_fwd, fwd_task_file.replace("tasks.yaml", "mission.yaml"))
    print(f"  -> Generated Forward Mission: {mission_name_fwd}")

    # Generate and save reverse mission
    rev_task_file = os.path.join(output_dir, f"{segment_name}_Reverse_tasks.yaml")
    save_task_list(reverse_task_list, rev_task_file)

    mission_name_rev = f"{segment_name}_Reverse_Mission"
    final_mission_rev = process_mission_generation(reverse_task_list, env, mission_name_rev)
    save_mission(final_mission_rev, rev_task_file.replace("tasks.yaml", "mission.yaml"))
    print(f"  -> Generated Reverse Mission: {mission_name_rev}")


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point for mission generation."""
    parser = argparse.ArgumentParser(parents=[env_info_parser()])
    args = parser.parse_args()

    env = load_base_environment(args.environment)
    entries = load_config(args.config)

    task_output_dir = "generated_tasks"
    os.makedirs(task_output_dir, exist_ok=True)

    print("--- Starting Generation Pipeline ---")

    for entry in entries:
        print(f"Processing config entry: {entry['name']}")

        mission_chunks = generate_waypoints_for_segment(entry, env)
        generate_and_save_missions(entry["name"], mission_chunks, env, task_output_dir)

    # Save final environment
    env_filename = args.output if args.output.endswith(".yaml") else f"{args.output}.yaml"
    save_environment(env, env_filename)
    print(f"--- Environment saved to {env_filename} ---")


if __name__ == "__main__":
    main()
