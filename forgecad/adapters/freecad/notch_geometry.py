"""FreeCAD geometry helpers for ForgeCAD tube notches."""

import FreeCAD
import Part


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
    member being cut.
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

    extension = float(
        extension
    )

    if extension < 0:
        raise ValueError(
            "Axis extension cannot be negative."
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


def extended_member_endpoints(
    start,
    end,
    start_extension=0.0,
    end_extension=0.0,
):
    """
    Return physical member endpoints after fabrication extension.

    Start and end extensions are independent because a member may
    require additional stock at only one joint.
    """

    start_extension = float(
        start_extension
    )

    end_extension = float(
        end_extension
    )

    if start_extension < 0:
        raise ValueError(
            "Member start extension cannot be negative."
        )

    if end_extension < 0:
        raise ValueError(
            "Member end extension cannot be negative."
        )

    direction = vector_between(
        start,
        end,
    )

    length = direction.Length

    if length <= 0:
        raise ValueError(
            "Cannot extend a zero-length member."
        )

    unit = FreeCAD.Vector(
        direction.x / length,
        direction.y / length,
        direction.z / length,
    )

    physical_start = FreeCAD.Vector(
        start.x
        - unit.x * start_extension,
        start.y
        - unit.y * start_extension,
        start.z
        - unit.z * start_extension,
    )

    physical_end = FreeCAD.Vector(
        end.x
        + unit.x * end_extension,
        end.y
        + unit.y * end_extension,
        end.z
        + unit.z * end_extension,
    )

    return (
        physical_start,
        physical_end,
    )


def design_member_length(
    start,
    end,
):
    """Return the original design-centerline member length."""

    return vector_between(
        start,
        end,
    ).Length


def build_through_tube_cutting_tool(
    start,
    end,
    outside_diameter,
    extension=None,
):
    """
    Build a solid cylindrical cutting tool for a target tube.

    The cutter represents the target tube's outside surface.
    Subtracting it from another tube produces the cope.
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
    plain_shape_builder,
):
    """
    Build a tube and cope it against a target tube.

    branch_start and branch_end are the physical fabrication
    endpoints. They may extend beyond the original design node.
    """

    branch_shape, branch_length = (
        plain_shape_builder(
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
