"""
Geometry and mathematical calculations for waypoint generation.
"""

import math
from typing import List


def calculate_distance(start: List[float], end: List[float]) -> float:
    """Calculate Euclidean distance between two 3D points."""
    return math.sqrt(
        (start[0] - end[0]) ** 2 +
        (start[1] - end[1]) ** 2 +
        (start[2] - end[2]) ** 2
    )


def calculate_waypoint_position(
    start: List[float],
    end: List[float],
    spacing: float,
    index: int,
    distance: float
) -> List[float]:
    """Calculate position of a waypoint along a line segment."""
    ratio = index * spacing / distance if distance > 0 else 0
    return [
        start[0] + (end[0] - start[0]) * ratio,
        start[1] + (end[1] - start[1]) * ratio,
        start[2] + (end[2] - start[2]) * ratio,
    ]


def calculate_normalized_direction(start: List[float], end: List[float]) -> List[float]:
    """
    Calculate normalized direction vector from start to end.

    Args:
        start: Starting position [x, y, z]
        end: Ending position [x, y, z]

    Returns:
        Normalized direction vector [dx, dy, dz]
    """
    distance = calculate_distance(start, end)
    if distance == 0:
        return [0.0, 0.0, 0.0]

    return [
        (end[0] - start[0]) / distance,
        (end[1] - start[1]) / distance,
        (end[2] - start[2]) / distance,
    ]


def offset_position(
    position: List[float],
    direction: List[float],
    distance: float
) -> List[float]:
    """
    Calculate a new position offset along a direction vector.

    Args:
        position: Starting position [x, y, z]
        direction: Direction vector [dx, dy, dz] (should be normalized)
        distance: Distance to offset (positive or negative)

    Returns:
        New position [x, y, z]
    """
    return [
        position[0] + direction[0] * distance,
        position[1] + direction[1] * distance,
        position[2] + direction[2] * distance,
    ]
