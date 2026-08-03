from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from forgecad.fabrication.material import Material
from forgecad.fabrication.node import Node
from forgecad.fabrication.tube_profile import TubeProfile


@dataclass(frozen=True, slots=True)
class Member:
    """Represents a structural tube between two nodes."""

    start_node: Node
    end_node: Node
    profile: TubeProfile
    material: Material

    @property
    def length(self) -> float:
        """Return member centerline length in millimeters."""

        dx = self.end_node.x - self.start_node.x
        dy = self.end_node.y - self.start_node.y
        dz = self.end_node.z - self.start_node.z

        return sqrt(
            dx**2 +
            dy**2 +
            dz**2
        )
    