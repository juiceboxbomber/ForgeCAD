"""FreeCAD geometry helpers for ForgeCAD tube notches."""

import FreeCAD
import Part

from forgecad.adapters.freecad.member_object import (
    build_tube_shape,
)


def vector_between(
    start,
    end,
):
    """Return the FreeCAD vector from start to end."""

    return FreeCAD.Vector(
        end.x - start.x,
        end.y - start.y,
        end.z - start.z,
    )


def extended_axis_endpoints(
    start,
    end,
    extension,
):
    """
    Extend a line segment beyond both endpoints.

    This is useful for Boolean cutting tools because the
    cutting cylinder should extend completely through the
    branch tube.
    """

    direction = vector_between(
        start,
        end,
    )

    length = direction.Length

    if length <= 0:
        raise ValueError(
            "Cannot extend a zero-length axis."
        )

    unit = FreeCAD.Vector(
        direction.x / length,
        direction.y / length,
        direction.z / length,
    )

    extended_start = FreeCAD.Vector(
        start.x - unit.x * extension,
        start.y - unit.y * extension,
        start.z - unit.z * extension,
    )

    extended_end = FreeCAD.Vector(
        end.x + unit.x * extension,
        end.y + unit.y * extension,
        end.z + unit.z * extension,
    )

    return (
        extended_start,
        extended_end,
    )


def build_through_tube_cutting_tool(
    start,
    end,
    outside_diameter,
    extension=None,
):
    """
    Build a solid cylindrical cutting tool for a through tube.

    The cutter represents the through tube's outside surface.
    Subtracting it from a branch tube produces the cope.
    """

    outside_diameter = float(
        outside_diameter
    )

    if outside_diameter <= 0:
        raise ValueError(
            "Through tube outside diameter must "
            "be greater than zero."
        )

    if extension is None:
        extension = (
            outside_diameter * 2.0
        )

    extension = float(
        extension
    )

    if extension < 0:
        raise ValueError(
            "Cutting-tool extension cannot be negative."
        )

    extended_start, extended_end = (
        extended_axis_endpoints(
            start,
            end,
            extension,
        )
    )

    direction = vector_between(
        extended_start,
        extended_end,
    )

    length = direction.Length

    radius = (
        outside_diameter / 2.0
    )

    return Part.makeCylinder(
        radius,
        length,
        extended_start,
        direction,
    )


def cope_tube_shape(
    branch_start,
    branch_end,
    branch_profile,
    through_start,
    through_end,
    through_outside_diameter,
):
    """
    Build a branch tube and cope it against a through tube.

    The returned shape is the branch tube with the through
    tube's outside cylindrical volume removed.
    """

    branch_shape, branch_length = (
        build_tube_shape(
            branch_start,
            branch_end,
            branch_profile,
        )
    )

    cutter = (
        build_through_tube_cutting_tool(
            through_start,
            through_end,
            through_outside_diameter,
        )
    )

    coped_shape = branch_shape.cut(
        cutter
    )

    return (
        coped_shape,
        branch_length,
    )
