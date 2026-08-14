"""Tube-bend domain definitions for ForgeCAD."""

from dataclasses import dataclass
from math import radians, tan


@dataclass(frozen=True, slots=True)
class Bend:
    """
    Describe one physical tube bend on the tube centerline.

    angle_degrees
        Included bend angle through which the tube centerline turns.

    centerline_radius
        Radius from the bend center to the tube centerline, in millimeters.

    rotation_degrees
        Rotation of the bend plane around the incoming straight tube axis.
        This is the value a fabricator would commonly use to clock a later
        bend relative to the previous bend plane.
    """

    angle_degrees: float
    centerline_radius: float
    rotation_degrees: float = 0.0

    def __post_init__(self) -> None:
        angle = float(
            self.angle_degrees
        )
        radius = float(
            self.centerline_radius
        )
        rotation = float(
            self.rotation_degrees
        )

        if angle <= 0.0:
            raise ValueError(
                "Bend angle must be greater than zero degrees."
            )

        if angle >= 180.0:
            raise ValueError(
                "Bend angle must be less than 180 degrees."
            )

        if radius <= 0.0:
            raise ValueError(
                "Bend centerline radius must be greater than zero."
            )

        object.__setattr__(
            self,
            "angle_degrees",
            angle,
        )

        object.__setattr__(
            self,
            "centerline_radius",
            radius,
        )

        object.__setattr__(
            self,
            "rotation_degrees",
            rotation % 360.0,
        )

    @property
    def angle_radians(self) -> float:
        """Return bend angle in radians."""

        return radians(
            self.angle_degrees
        )

    @property
    def arc_length(self) -> float:
        """Return developed centerline length through the bend."""

        return (
            self.centerline_radius
            * self.angle_radians
        )

    @property
    def tangent_setback(self) -> float:
        """
        Return tangent setback from the theoretical intersection.

        For two straight centerlines meeting at the bend angle:

            setback = CLR * tan(angle / 2)
        """

        return (
            self.centerline_radius
            * tan(
                self.angle_radians
                / 2.0
            )
        )
