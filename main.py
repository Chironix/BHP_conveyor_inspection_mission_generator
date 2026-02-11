#!/usr/bin/env python3
"""
ANYmal mission and environment generator for conveyor belt inspection.

Generates navigation waypoints and inspection points along linear segments,
then creates forward and reverse mission files for the ANYmal robot.
"""

import argparse
import os

from field_utils.file_io import load_config, load_base_environment, save_environment
from field_utils.environment_builder import generate_waypoints_for_segment
from field_utils.mission_generator import generate_and_save_missions


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

    # Create output directory
    task_output_dir = "generated_tasks"
    os.makedirs(task_output_dir, exist_ok=True)

    print("--- Starting Generation Pipeline ---")

    # Process each segment
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
