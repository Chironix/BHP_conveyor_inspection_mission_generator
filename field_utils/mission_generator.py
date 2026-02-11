"""
Mission generation and file output handling.
"""

import os
from typing import Dict, List, Any

from .models import Environment
from .task_factory import process_mission_generation
from .file_io import save_mission


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
    mission_name_fwd = f"{segment_name}_Forward_Mission"
    final_mission_fwd = process_mission_generation(forward_task_list, env, mission_name_fwd)
    fwd_mission_file = os.path.join(output_dir, f"{segment_name}_Forward_mission.yaml")
    save_mission(final_mission_fwd, fwd_mission_file)
    print(f"  -> Generated Forward Mission: {mission_name_fwd}")

    # Generate and save reverse mission
    mission_name_rev = f"{segment_name}_Reverse_Mission"
    final_mission_rev = process_mission_generation(reverse_task_list, env, mission_name_rev)
    rev_mission_file = os.path.join(output_dir, f"{segment_name}_Reverse_mission.yaml")
    save_mission(final_mission_rev, rev_mission_file)
    print(f"  -> Generated Reverse Mission: {mission_name_rev}")
