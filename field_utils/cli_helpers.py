import argparse


def env_info_parser() -> argparse.ArgumentParser:
    """
    Parse the mission generation arguments.
    :return: Argument parser.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--environment",
        "-e",
        type=str,
        default="environment.yaml",
        help="Name of the related environment file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="environment_out.yaml",
        help="Name of the processed environment file.",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config_env.yaml",
        help="Name of the config file for generating the environment file.",
    )
    return parser
