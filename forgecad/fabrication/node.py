"""Node definitions for ForgeCAD."""

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True, slots=True)
class Node:
    """Represents a point in 3D space."""

    x: float
    y: float
    z: float

    def distance_to(self, other: "Node") -> float:
        """Return the distance to another node in millimeters."""
        dx = other.x - self.x
        dy = other.y - self.y
        dz = other.z - self.z

        return sqrt(dx * dx + dy * dy + dz * dz)
    