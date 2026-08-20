"""First-class ForgeCAD joint constraint models."""

from dataclasses import dataclass
from enum import Enum

from forgecad.geometry.point import Point3D


class JointConstraintKind(
    str,
    Enum,
):
    """Stable persisted identifiers for ForgeCAD joint constraints."""

    COLLINEAR_THROUGH = (
        "collinear_through"
    )


@dataclass(
    frozen=True,
    slots=True,
)
class CollinearThroughConstraint:
    """
    Preserve a joint on the axis of a straight-through member pair.

    The axis endpoints are stored explicitly so the constraint remains
    independent from any particular FreeCAD object representation.
    """

    axis_start: Point3D
    axis_end: Point3D

    @property
    def kind(
        self,
    ) -> JointConstraintKind:
        """Return this constraint's stable kind."""

        return (
            JointConstraintKind.COLLINEAR_THROUGH
        )
