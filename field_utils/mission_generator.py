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
    output_dir: str
) -> None:
    """Generate mission and save to file."""
    # Flatten chunks: A -> B -> C
    task_list = [task for chunk in mission_chunks for task in chunk]

    # Generate and save mission
    mission_name = f"{segment_name}_Mission"
    mission = process_mission_generation(task_list, env, mission_name)
    mission_file = os.path.join(output_dir, f"{segment_name}_mission.yaml")
    save_mission(mission, mission_file)
    print(f"  -> Generated Mission: {mission_name}")
