"""
Mission generation and file output handling.
"""

import os
from typing import Dict, List, Any

from .models import Environment
from .task_factory import process_mission_generation
from .file_io import save_mission


def generate_and_save_mission(
    segment_name: str,
    mission_chunks: List[List[Dict[str, Any]]],
    env: Environment,
    output_dir: str,
    mission_suffix: str = ""
) -> None:
    """
    Generate mission from task chunks and save to file.

    Args:
        segment_name: Name of the segment (e.g., "S1_", "S2_")
        mission_chunks: List of task chunks (each chunk groups tasks for a waypoint)
        env: Environment for validation
        output_dir: Directory to save mission files
        mission_suffix: Optional suffix for mission name (e.g., "Return", "Continue")
    """
    # Flatten chunks into task list
    task_list = [task for chunk in mission_chunks for task in chunk]

    # Generate mission from task list
    suffix = f"_{mission_suffix}" if mission_suffix else ""
    mission_name = f"{segment_name}{suffix}_Mission"
    mission = process_mission_generation(task_list, env, mission_name)

    # Save mission file
    filename_suffix = f"_{mission_suffix.lower()}" if mission_suffix else ""
    mission_file = os.path.join(output_dir, f"{segment_name}{filename_suffix}_mission.yaml")
    save_mission(mission, mission_file)
    print(f"  -> Generated Mission: {mission_name}")
