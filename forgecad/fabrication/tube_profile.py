from __future__ import annotations

from dataclasses import dataclass
from math import pi


@dataclass(frozen=True, slots=True)
class TubeProfile:
    """Defines a round tube profile.

    All dimensions are stored internally in millimeters.
    """

    outside_diameter_mm: float
    wall_thickness_mm: float

    def __post_init__(self) -> None:
        if self.outside_diameter_mm <= 0:
            raise ValueError("Outside diameter must be greater than zero.")

        if self.wall_thickness_mm <= 0:
            raise ValueError("Wall thickness must be greater than zero.")

        if self.wall_thickness_mm >= self.outside_diameter_mm / 2:
            raise ValueError(
                "Wall thickness must be less than half the outside diameter."
            )

    @property
    def inside_diameter_mm(self) -> float:
        return self.outside_diameter_mm - (2 * self.wall_thickness_mm)

    @property
    def cross_section_area_mm2(self) -> float:
        return (pi / 4) * (
            self.outside_diameter_mm**2
            - self.inside_diameter_mm**2
        )
    