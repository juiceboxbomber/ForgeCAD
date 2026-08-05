"""Tube profile definitions for ForgeCAD."""

from dataclasses import dataclass
from math import pi


@dataclass(frozen=True, slots=True)
class TubeProfile:
    """Represents the geometry of round tubing."""

    outside_diameter: float  # mm
    wall_thickness: float    # mm

    def __post_init__(self) -> None:
        if self.outside_diameter <= 0:
            raise ValueError("Outside diameter must be greater than zero.")

        if self.wall_thickness <= 0:
            raise ValueError("Wall thickness must be greater than zero.")

        if self.wall_thickness >= self.outside_diameter / 2:
            raise ValueError(
                "Wall thickness must be less than the tube radius."
            )

    @property
    def inside_diameter(self) -> float:
        return self.outside_diameter - (2 * self.wall_thickness)

    @property
    def cross_sectional_area(self) -> float:
        od = self.outside_diameter
        id_ = self.inside_diameter
        return (pi / 4.0) * (od**2 - id_**2)

    @property
    def area_moment_of_inertia(self) -> float:
        od = self.outside_diameter
        id_ = self.inside_diameter
        return (pi / 64.0) * (od**4 - id_**4)

    @property
    def section_modulus(self) -> float:
        return self.area_moment_of_inertia / (self.outside_diameter / 2.0)
    