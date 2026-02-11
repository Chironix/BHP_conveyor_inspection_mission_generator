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
