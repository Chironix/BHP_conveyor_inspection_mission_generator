#!/usr/bin/env python3
"""
ANYmal mission and environment generator for conveyor belt inspection.

Generates navigation waypoints and inspection points along linear segments,
then creates mission files for the ANYmal robot.
"""

import argparse
import os

from field_utils.file_io import load_config, load_base_environment, save_environment
from field_utils.environment_builder import generate_waypoints_for_segment, add_end_docking_station
from field_utils.mission_generator import generate_and_save_mission


def main():
    """Main entry point for mission generation."""
    parser = argparse.ArgumentParser(
        description="Generate ANYmal inspection missions for conveyor belt segments"
    )
    parser.add_argument(
        "--environment", "-e",
        type=str,
        default="environment.yaml",
        help="Base environment file with docking station"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config_env.yaml",
        help="Configuration file defining conveyor segments"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="environment_out.yaml",
        help="Output environment file name"
    )
    args = parser.parse_args()

    # Load base environment and configuration
    env = load_base_environment(args.environment)
    entries = load_config(args.config)

    # Add second docking station at the end of the tunnel (S4 end position)
    s4_entry = next((e for e in entries if e["name"] == "S4_"), None)
    if s4_entry:
        add_end_docking_station(env, s4_entry)

    # Create output directory
    task_output_dir = "generated_tasks"
    os.makedirs(task_output_dir, exist_ok=True)

    print("--- Starting Generation Pipeline ---")

    # Process each segment
    for entry in entries:
        print(f"Processing config entry: {entry['name']}")
        mission_chunks = generate_waypoints_for_segment(entry, env)

        segment_name = entry["name"]

        # Special handling for segment 3: generate two missions
        if segment_name == "S3_":
            # Mission that returns to dock
            return_chunks = mission_chunks.copy()
            return_chunks.append([{
                "name": "DockingStation1NavigationGoal",
                "type": "navigation_goal"
            }])
            generate_and_save_mission(
                segment_name, return_chunks, env, task_output_dir,
                mission_suffix="Return"
            )

            # Mission that continues to next segment (navigates to end of tunnel)
            continue_chunks = mission_chunks.copy()
            continue_chunks.append([{
                "name": "DockingStation2NavigationGoal",
                "type": "navigation_goal"
            }])
            generate_and_save_mission(
                segment_name, continue_chunks, env, task_output_dir,
                mission_suffix="Continue"
            )

        # Special handling for segment 4: no return to dock
        elif segment_name == "S4_":
            # S4 ends at the last inspection, no additional navigation
            generate_and_save_mission(
                segment_name, mission_chunks, env, task_output_dir
            )

        # All other segments: return to dock
        else:
            mission_chunks.append([{
                "name": "DockingStation1NavigationGoal",
                "type": "navigation_goal"
            }])
            generate_and_save_mission(
                segment_name, mission_chunks, env, task_output_dir
            )

    # Save final environment
    env_filename = args.output if args.output.endswith(".yaml") else f"{args.output}.yaml"
    save_environment(env, env_filename)
    print(f"--- Environment saved to {env_filename} ---")


if __name__ == "__main__":
    main()
