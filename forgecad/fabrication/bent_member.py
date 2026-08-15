"""Bent structural-member definitions for ForgeCAD."""

from dataclasses import dataclass, field

from forgecad.geometry import Vector3D

from .node import Node
from .tube_path import BentTube


@dataclass(frozen=True, slots=True)
class BentMember:
    """Represents one structural frame member made from a bent tube."""

    start: Node
    end: Node
    tube: BentTube

    initial_direction: Vector3D = field(
        default_factory=lambda: Vector3D(
            1.0,
            0.0,
            0.0,
        )
    )

    initial_bend_normal: Vector3D = field(
        default_factory=lambda: Vector3D(
            0.0,
            0.0,
            1.0,
        )
    )

    def __post_init__(self) -> None:
        direction = (
            self.initial_direction
            .normalized()
        )

        normal = (
            self.initial_bend_normal
            .normalized()
        )

        if abs(
            direction.dot(
                normal
            )
        ) > 1e-6:
            raise ValueError(
                "Bent-member initial direction and "
                "bend normal must be perpendicular."
            )

        object.__setattr__(
            self,
            "initial_direction",
            direction,
        )

        object.__setattr__(
            self,
            "initial_bend_normal",
            normal,
        )

    @property
    def profile(self):
        """Return the tube profile used by this member."""

        return self.tube.profile

    @property
    def material(self):
        """Return the material used by this member."""

        return self.tube.material

    @property
    def length(self) -> float:
        """Return developed centerline length in millimeters."""

        return self.tube.developed_length
    