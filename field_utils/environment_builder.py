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
    DockingStation,
)


def add_end_docking_station(env: Environment, s4_config: Dict[str, Any]) -> None:
    """
    Add a second docking station at the end of the tunnel (S4 end position).

    Args:
        env: Environment to add the docking station to
        s4_config: Configuration entry for S4 segment
    """
    end_pos = s4_config["end"]
    start_pos = s4_config["start"]

    # Calculate direction vector from start to end
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    dz = end_pos[2] - start_pos[2]
    length = (dx**2 + dy**2 + dz**2)**0.5

    # Normalize direction vector
    dir_x = dx / length
    dir_y = dy / length
    dir_z = dz / length

    # Position docking station 2 meters back from end
    offset_distance = 2.0
    dock2_pos = [
        end_pos[0] - dir_x * offset_distance,
        end_pos[1] - dir_y * offset_distance,
        end_pos[2] - dir_z * offset_distance
    ]

    # Create docking station
    dock2 = DockingStation("DockingStation2", "Docking Station 2")
    dock2.pose.pose.position.x = dock2_pos[0]
    dock2.pose.pose.position.y = dock2_pos[1]
    dock2.pose.pose.position.z = dock2_pos[2]
    dock2.pose.pose.orientation.w = s4_config["orientation"]["w"]
    dock2.pose.pose.orientation.x = s4_config["orientation"]["x"]
    dock2.pose.pose.orientation.y = s4_config["orientation"]["y"]
    dock2.pose.pose.orientation.z = s4_config["orientation"]["z"]
    dock2.pose.set_translation_tolerance(0.05)
    dock2.pose.set_rotation_tolerance(0.1)
    env.add_object(dock2)

    # Create navigation goal 1 meter further back from docking station
    nav_offset = 1.0
    dock2_nav_pos = [
        dock2_pos[0] - dir_x * nav_offset,
        dock2_pos[1] - dir_y * nav_offset,
        dock2_pos[2] - dir_z * nav_offset
    ]

    dock2_nav = NavigationGoal("DockingStation2NavigationGoal", "Docking Station 2 Navigation Goal")
    dock2_nav.pose.pose.position.x = dock2_nav_pos[0]
    dock2_nav.pose.pose.position.y = dock2_nav_pos[1]
    dock2_nav.pose.pose.position.z = dock2_nav_pos[2]
    dock2_nav.pose.pose.orientation.w = s4_config["orientation"]["w"]
    dock2_nav.pose.pose.orientation.x = s4_config["orientation"]["x"]
    dock2_nav.pose.pose.orientation.y = s4_config["orientation"]["y"]
    dock2_nav.pose.pose.orientation.z = s4_config["orientation"]["z"]
    dock2_nav.pose.set_translation_tolerance(0.05)
    dock2_nav.pose.set_rotation_tolerance(0.1)
    env.add_object(dock2_nav)

    print(f"Added DockingStation2 at position [{dock2_pos[0]:.2f}, {dock2_pos[1]:.2f}, {dock2_pos[2]:.2f}]")


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
