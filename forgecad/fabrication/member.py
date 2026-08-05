"""Member definitions for ForgeCAD."""

from dataclasses import dataclass

from .material import Material
from .node import Node
from .tube_profile import TubeProfile


@dataclass(frozen=True, slots=True)
class Member:
    """Represents a single tube between two nodes."""

    start: Node
    end: Node
    profile: TubeProfile
    material: Material

    @property
    def length(self) -> float:
        """Return member length in millimeters."""
        return self.start.distance_to(self.end)
    