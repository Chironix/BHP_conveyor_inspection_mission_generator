#!/usr/bin/env python3

import argparse
import yaml
import copy
import math
import os

from field_utils.yaml_dumper import AnyboticsYamlDumper
from field_utils.cli_helpers import env_info_parser
from field_utils.environment_utils import (
    load_environment,
    get_item_from_name,
    thermal_inspection,
    nav_goal,
    nav_zone,
    visual_inspection,
    relation,
    set_coordinate,
    set_orientation,
)
from field_utils.mission_utils import (
    set_next_task_name,
    set_last_task_transitions,
    mission_template,
    undock_task,
    dock_task,
    inspection_task,
    simple_inspection_task,
    navigation_task,
    sleep_task,
)

# --- CONFIGURATION DATA (From generate_mission.py) ---
task_data = {
    "visual_inspection_thermal": {
        "task_prefix": "Inspect",
        "item_suffix": "VIT",
        "plugin": "visual_inspection_thermal_behavior_plugins",
        "mission_task": inspection_task,
    },
    "inspection_intelligence": {
        "task_prefix": "Inspect",
        "item_suffix": "II",
        "plugin": "inspection_intelligence_behavior_plugins",
        "mission_task": inspection_task,
    },
    "auditive_inspection_frequency": {
        "task_prefix": "Inspect",
        "item_suffix": "AudioFreq",
        "plugin": "auditive_inspection_frequency_behavior_plugins",
        "mission_task": inspection_task,
    },
    "visual_inspection_simple": {
        "task_prefix": "Inspect",
        "item_suffix": "VIS",
        "plugin": "visual_inspection_simple_behavior_plugins",
        "mission_task": simple_inspection_task,
    },
    "auditive_inspection_simple": {
        "task_prefix": "Inspect",
        "item_suffix": "AudioS",
        "plugin": "auditive_inspection_simple_behavior_plugins",
        "mission_task": simple_inspection_task,
    },
    "visual_inspection_video_recording": {
        "task_prefix": "Record",
        "item_suffix": "VSVR",
        "plugin": "visual_inspection_video_recording_behavior_plugins",
        "mission_task": simple_inspection_task,
    },
    "undock": {
        "task_prefix": "",
        "item_suffix": "",
        "plugin": "system_behavior_plugins",
        "mission_task": undock_task,
    },
    "dock": {
        "task_prefix": "",
        "item_suffix": "",
        "plugin": "system_behavior_plugins",
        "mission_task": dock_task,
    },
    "navigation_goal": {
        "task_prefix": "Navigate to",
        "item_suffix": "NavGoal",
        "plugin": "navigation_behavior_plugins",
        "mission_task": navigation_task,
    },
    "sleep": {
        "task_prefix": "",
        "item_suffix": "S",
        "plugin": "basic_behavior_plugins",
        "mission_task": sleep_task,
    },
}

simplified_task_type = {
    "dock": "dock",
    "undock": "undock",
    "sleep": "sleep",
}

# --- CONFIGURATION DATA (From generate_straight_environment.py) ---
item_data = {
    "thermal_inspection": {"suffix": "VIT", "type_data": thermal_inspection},
    "nav_goal": {"suffix": "NavGoal", "type_data": nav_goal},
    "nav_zone": {"suffix": "NavZone", "type_data": nav_zone},
    "visual_inspection": {"suffix": "VIS", "type_data": visual_inspection},
}


def create_task_entry(task, env):
    """
    Logic from generate_mission.py to convert a simple task into a full mission task.
    """
    # Convert simplified task type to real task type
    if "label" not in task:
        task["label"] = task["name"]

    if "type" in task:
        if task["type"] in simplified_task_type:
            task["type"] = simplified_task_type[task["type"]]
        else:
            # If type is provided but not simplified, assume it's valid
            pass
    else:
        # Try to infer type from environment
        envObject = get_item_from_name(env, task["name"])
        if envObject is None:
            print(
                f"Warning: Object '{task['name']}' not found in environment."
            )
            return None
        task["type"] = envObject["type"]

    if task["type"] in task_data:
        active_task_type = task_data[task["type"]]
        mission_task = copy.deepcopy(active_task_type["mission_task"])

        # Check existence in environment
        if (
            task["type"] not in simplified_task_type
            and get_item_from_name(env, task["name"]) is None
        ):
            # Try appending suffix
            if (
                get_item_from_name(
                    env, task["name"] + "-" + active_task_type["item_suffix"]
                )
                is None
            ):
                print(
                    f"Warning: Object '{task['name']}' not found in environment."
                )
            else:
                task["name"] = (
                    task["name"] + "-" + active_task_type["item_suffix"]
                )

        if task["type"] == "sleep" and "duration" in task:
            for setting in mission_task["settings"]:
                if setting["name"] == "duration":
                    setting["value"] = task["duration"]

        # Action handling
        if "action" in task:
            active_task_type_copy = copy.deepcopy(active_task_type)
            active_task_type_copy["action"] = task["action"]
            active_task_type = active_task_type_copy  # Use local copy to avoid mutating global
        elif "action" not in active_task_type:
            # Default action if not present
            pass

    else:
        print(f"Cannot create task of type: {task['type']}")
        return None

    # Add prefix and Suffix
    if active_task_type["task_prefix"]:
        mission_task["name"] = (
            active_task_type["task_prefix"] + " " + task["label"]
        )
    else:
        mission_task["name"] = task["label"]

    if (
        len(mission_task["settings"]) > 0
        and mission_task["settings"][0]["name"] != "duration"
    ):
        mission_task["settings"][0]["value"] = task["name"]

    mission_task["type"] = mission_task["type"].replace(
        "[plugin_name]", active_task_type["plugin"]
    )

    # Handle action replacement
    action_val = active_task_type.get(
        "action", "Inspect"
    )  # Default to Inspect if missing
    if "[plugin_action]" in mission_task["type"]:
        mission_task["type"] = mission_task["type"].replace(
            "[plugin_action]", action_val
        )

    return mission_task


def process_mission_generation(task_list_data, env, mission_name):
    """
    Generates the full mission structure from a list of simple tasks.
    """
    mission_tasks = []
    initial_task = ""
    previous_task = None

    local_mission_template = copy.deepcopy(mission_template)

    for task in task_list_data:
        mission_task = create_task_entry(task, env)

        if mission_task is None:
            continue

        if previous_task is not None:
            set_next_task_name(previous_task, mission_task["name"])
        else:
            initial_task = mission_task["name"]

        mission_tasks.append(mission_task)
        previous_task = mission_task

    if previous_task is not None:
        set_last_task_transitions(previous_task)

    # Update mission settings
    for mission_setting in local_mission_template["settings"]:
        if mission_setting["name"] == "default_initial_state":
            mission_setting["value"] = initial_task
        elif mission_setting["name"] == "states":
            mission_setting["value"] = mission_tasks

    local_mission_template["name"] = mission_name
    return local_mission_template


def main():
    # Setup Argument Parser
    parser = argparse.ArgumentParser(parents=[env_info_parser()])
    args = parser.parse_args()

    # Load Base Environment
    try:
        env = load_environment(args.environment)
    except FileNotFoundError:
        print(
            f"Base environment file '{args.environment}' not found. Starting with empty environment."
        )
        env = {"objects": [], "object_relations": []}

    entries = load_environment(args.config)

    # Create directory for intermediate task files
    task_output_dir = "generated_tasks"
    os.makedirs(task_output_dir, exist_ok=True)

    print(f"--- Starting Generation Pipeline ---")

    for entry in entries:
        print(f"Processing config entry: {entry['name']}")

        dist = math.sqrt(
            math.pow(entry["start"][0] - entry["end"][0], 2)
            + math.pow(entry["start"][1] - entry["end"][1], 2)
            + math.pow(entry["start"][2] - entry["end"][2], 2)
        )
        n = int(dist / entry["spacing"])

        # We use a list of lists (chunks) to keep Nav+Inspect pairs together
        mission_chunks = []

        i = 0
        while i < (n + 1):
            current_chunk = (
                []
            )  # Holds tasks for this specific waypoint (Nav + Inspections)

            ratio = i * entry["spacing"] / dist if dist > 0 else 0
            actual_nav_pos = [
                entry["start"][0]
                + (entry["end"][0] - entry["start"][0]) * ratio,
                entry["start"][1]
                + (entry["end"][1] - entry["start"][1]) * ratio,
                entry["start"][2]
                + (entry["end"][2] - entry["start"][2]) * ratio,
            ]

            # 1. Create Nav Goal & Zone
            this_nav_goal = copy.deepcopy(nav_goal)
            set_coordinate(this_nav_goal, actual_nav_pos)
            this_nav_goal["name"] = entry["name"] + str(i) + "_NavGoal"
            this_nav_goal["label"] = this_nav_goal["name"]

            if "orientation" in entry:
                set_orientation(this_nav_goal, entry["orientation"])
            if "translation_tolerance" in entry:
                this_nav_goal["pose"]["tolerance"]["translation"] = entry[
                    "translation_tolerance"
                ]

            env["objects"].append(this_nav_goal)

            this_nav_zone = copy.deepcopy(nav_zone)
            this_nav_zone["name"] = entry["name"] + str(i) + "_NavZone"
            env["objects"].append(this_nav_zone)

            goal_to_zone = copy.deepcopy(relation)
            goal_to_zone["child"] = this_nav_goal["name"]
            goal_to_zone["parent"] = this_nav_zone["name"]
            if "object_relations" not in env:
                env["object_relations"] = []
            env["object_relations"].append(goal_to_zone)

            # TASK: Add Navigation to chunk
            current_chunk.append(
                {"name": this_nav_goal["name"], "type": "navigation_goal"}
            )

            # 2. Handle Inspections
            if "inspections" in entry:
                for inspection_entry in entry["inspections"]:
                    actual_item_pos = [
                        actual_nav_pos[0] + inspection_entry["offset"][0],
                        actual_nav_pos[1] + inspection_entry["offset"][1],
                        actual_nav_pos[2] + inspection_entry["offset"][2],
                    ]

                    type_info = item_data[inspection_entry["type"]]
                    this_inspection = copy.deepcopy(type_info["type_data"])
                    set_coordinate(this_inspection, actual_item_pos)

                    obj_name = (
                        entry["name"]
                        + str(i)
                        + inspection_entry["suffix"]
                        + type_info["suffix"]
                    )
                    this_inspection["name"] = obj_name
                    this_inspection["label"] = obj_name

                    # Apply custom orientation if present in config
                    if "orientation" in inspection_entry:
                        set_orientation(
                            this_inspection, inspection_entry["orientation"]
                        )

                    if inspection_entry["type"] == "visual_inspection":
                        if "width" in inspection_entry:
                            this_inspection["size"]["width"] = (
                                inspection_entry["width"]
                            )
                        if "height" in inspection_entry:
                            this_inspection["size"]["height"] = (
                                inspection_entry["height"]
                            )

                    env["objects"].append(this_inspection)

                    inspection_to_zone = copy.deepcopy(relation)
                    inspection_to_zone["child"] = this_nav_zone["name"]
                    inspection_to_zone["parent"] = this_inspection["name"]
                    env["object_relations"].append(inspection_to_zone)

                    # TASK: Add Inspection to chunk
                    task_type_map = {
                        "thermal_inspection": "visual_inspection_thermal",
                        "visual_inspection": "visual_inspection_simple",
                    }
                    mapped_type = task_type_map.get(
                        inspection_entry["type"], inspection_entry["type"]
                    )

                    current_chunk.append(
                        {
                            "name": obj_name,
                            "type": mapped_type,
                            "action": "InspectFromHere",
                        }
                    )

            # Add this location's tasks to the main list
            mission_chunks.append(current_chunk)
            i += 1

        # --- BUILD TASK LISTS ---

        # Flatten chunks for Forward Mission (A -> B -> C)
        forward_task_list = [
            task for chunk in mission_chunks for task in chunk
        ]

        # Reverse chunks but keep internal order for Reverse Mission (C -> B -> A)
        # We navigate to C then inspect C, then navigate to B...
        reverse_task_list = [
            task for chunk in reversed(mission_chunks) for task in chunk
        ]

        # --- GENERATE FORWARD MISSION ---
        fwd_task_file = os.path.join(
            task_output_dir, f"{entry['name']}_Forward_tasks.yaml"
        )
        with open(fwd_task_file, "w") as file:
            file.write(
                yaml.dump(
                    forward_task_list,
                    Dumper=AnyboticsYamlDumper,
                    default_flow_style=False,
                )
            )

        mission_name_fwd = f"{entry['name']}_Forward_Mission"
        final_mission_fwd = process_mission_generation(
            forward_task_list, env, mission_name_fwd
        )

        with open(
            fwd_task_file.replace("tasks.yaml", "mission.yaml"), "w"
        ) as file:
            file.write(
                yaml.dump(
                    final_mission_fwd,
                    Dumper=AnyboticsYamlDumper,
                    default_flow_style=False,
                )
            )
        print(f"  -> Generated Forward Mission: {mission_name_fwd}")

        # --- GENERATE REVERSE MISSION ---
        rev_task_file = os.path.join(
            task_output_dir, f"{entry['name']}_Reverse_tasks.yaml"
        )
        with open(rev_task_file, "w") as file:
            file.write(
                yaml.dump(
                    reverse_task_list,
                    Dumper=AnyboticsYamlDumper,
                    default_flow_style=False,
                )
            )

        mission_name_rev = f"{entry['name']}_Reverse_Mission"
        final_mission_rev = process_mission_generation(
            reverse_task_list, env, mission_name_rev
        )

        with open(
            rev_task_file.replace("tasks.yaml", "mission.yaml"), "w"
        ) as file:
            file.write(
                yaml.dump(
                    final_mission_rev,
                    Dumper=AnyboticsYamlDumper,
                    default_flow_style=False,
                )
            )
        print(f"  -> Generated Reverse Mission: {mission_name_rev}")

    # --- SAVE ENVIRONMENT ---
    env_filename = args.output + ".yaml"
    with open(env_filename, "w") as file:
        file.write(
            yaml.dump(
                env, Dumper=AnyboticsYamlDumper, default_flow_style=False
            )
        )
    print(f"--- Environment saved to {env_filename} ---")


if __name__ == "__main__":
    main()
