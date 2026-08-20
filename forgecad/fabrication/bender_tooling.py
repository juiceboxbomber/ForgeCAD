"""Tubing-bender tooling domain definitions for ForgeCAD."""

from dataclasses import dataclass
from enum import Enum


class BendMarkReference(str, Enum):
    """Reference convention used for a physical bend mark."""

    START_TANGENT = "start_tangent"
    CENTER_OF_BEND = "center_of_bend"


@dataclass(frozen=True, slots=True)
class BenderTooling:
    """Describe one tubing-bender die and calibrated setup."""

    name: str
    centerline_radius_mm: float
    mark_reference: BendMarkReference = BendMarkReference.START_TANGENT
    mark_offset_mm: float = 0.0
    angle_compensation_degrees: float = 0.0

    def __post_init__(self) -> None:
        name = self.name.strip()
        radius = float(self.centerline_radius_mm)

        if not name:
            raise ValueError(
                "Bender tooling name cannot be empty."
            )

        if radius <= 0.0:
            raise ValueError(
                "Bender tooling centerline radius must be greater than zero."
            )

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "centerline_radius_mm", radius)
        object.__setattr__(
            self,
            "mark_reference",
            BendMarkReference(self.mark_reference),
        )
        object.__setattr__(
            self,
            "mark_offset_mm",
            float(self.mark_offset_mm),
        )
        object.__setattr__(
            self,
            "angle_compensation_degrees",
            float(self.angle_compensation_degrees),
        )
