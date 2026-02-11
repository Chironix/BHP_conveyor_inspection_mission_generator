"""
File I/O operations for loading and saving YAML configuration and output files.
"""

import yaml
from typing import List, Dict, Any

from .yaml_dumper import AnyboticsYamlDumper
from .models import (
    Environment,
    NavigationGoal,
    DockingStation,
    Mission,
)


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
