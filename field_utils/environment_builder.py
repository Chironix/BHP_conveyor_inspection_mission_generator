"""
Environment object creation for waypoints and inspection points.
"""

from typing import Dict, List, Any, Optional, Tuple

from .geometry import calculate_distance, calculate_waypoint_position
from .models import (
    Environment,
    NavigationGoal,
    NavigationZone,
    ThermalInspectionPoint,
    VisualInspectionPoint,
)


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
