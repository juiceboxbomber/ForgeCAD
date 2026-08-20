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


def vector_length(
    vector,
):
    """Return vector magnitude."""

    return (
        vector.x * vector.x
        + vector.y * vector.y
        + vector.z * vector.z
    ) ** 0.5


def unit_vector(
    start,
    end,
):
    """Return a unit vector from start to end."""

    direction = vector_between(
        start,
        end,
    )

    length = vector_length(
        direction
    )

    if length <= 0:
        raise ValueError(
            "Cannot create a direction from "
            "coincident points."
        )

    return FreeCAD.Vector(
        direction.x / length,
        direction.y / length,
        direction.z / length,
    )


def cross_length(
    first,
    second,
):
    """Return the magnitude of the vector cross product."""

    x = (
        first.y * second.z
        - first.z * second.y
    )

    y = (
        first.z * second.x
        - first.x * second.z
    )

    z = (
        first.x * second.y
        - first.y * second.x
    )

    return (
        x * x
        + y * y
        + z * z
    ) ** 0.5


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


def point_to_axis_distance(
    point,
    axis_start,
    axis_end,
):
    """Return perpendicular distance from a point to an axis."""

    axis = vector_between(
        axis_start,
        axis_end,
    )

    axis_length = vector_length(
        axis
    )

    if axis_length <= 0:
        raise ValueError(
            "Cannot measure distance to "
            "a zero-length axis."
        )

    relative = FreeCAD.Vector(
        point.x - axis_start.x,
        point.y - axis_start.y,
        point.z - axis_start.z,
    )

    return (
        cross_length(
            relative,
            axis,
        )
        / axis_length
    )


def axis_intersection_sine(
    first_start,
    first_end,
    second_start,
    second_end,
):
    """
    Return sine of the acute angle between two centerline axes.

    Using the cross-product magnitude avoids dependence on
    angle orientation and works for both 90-degree and angled
    tube joints.
    """

    first = vector_between(
        first_start,
        first_end,
    )

    second = vector_between(
        second_start,
        second_end,
    )

    first_length = vector_length(
        first
    )

    second_length = vector_length(
        second
    )

    if (
        first_length <= 0
        or second_length <= 0
    ):
        raise ValueError(
            "Cannot calculate angle for "
            "a zero-length tube axis."
        )

    sine = (
        cross_length(
            first,
            second,
        )
        / (
            first_length
            * second_length
        )
    )

    if sine <= 1e-9:
        raise ValueError(
            "Cannot create a cope for "
            "collinear tube axes."
        )

    return sine


def temporary_cope_extension(
    branch_start,
    branch_end,
    branch_profile,
    through_start,
    through_end,
    through_outside_diameter,
):
    """
    Return temporary branch stock required for cope generation.

    This extension is NOT a ForgeCAD fabrication extension.

    It exists only while constructing the Boolean cope. The
    excess material on the far side of the target tube is
    discarded after cutting.
    """

    sine = axis_intersection_sine(
        branch_start,
        branch_end,
        through_start,
        through_end,
    )

    through_radius = (
        float(
            through_outside_diameter
        )
        / 2.0
    )

    branch_radius = (
        float(
            branch_profile.outside_diameter
        )
        / 2.0
    )

    # Use generous temporary stock. Any disconnected material
    # beyond the through tube is discarded after the Boolean.
    return (
        (
            through_radius
            + branch_radius
        )
        / sine
        + max(
            through_radius,
            branch_radius,
        )
    )


def temporary_branch_endpoints_for_cope(
    branch_start,
    branch_end,
    branch_profile,
    through_start,
    through_end,
    through_outside_diameter,
):
    """
    Extend only the branch endpoint located at the joint.

    The opposite endpoint is the keep side of the finished tube.
    """

    start_distance = (
        point_to_axis_distance(
            branch_start,
            through_start,
            through_end,
        )
    )

    end_distance = (
        point_to_axis_distance(
            branch_end,
            through_start,
            through_end,
        )
    )

    extension = (
        temporary_cope_extension(
            branch_start,
            branch_end,
            branch_profile,
            through_start,
            through_end,
            through_outside_diameter,
        )
    )

    direction = unit_vector(
        branch_start,
        branch_end,
    )

    if start_distance <= end_distance:
        temporary_start = FreeCAD.Vector(
            branch_start.x
            - direction.x
            * extension,
            branch_start.y
            - direction.y
            * extension,
            branch_start.z
            - direction.z
            * extension,
        )

        temporary_end = FreeCAD.Vector(
            branch_end.x,
            branch_end.y,
            branch_end.z,
        )

        keep_point = FreeCAD.Vector(
            branch_end.x,
            branch_end.y,
            branch_end.z,
        )

        return (
            temporary_start,
            temporary_end,
            keep_point,
        )

    temporary_start = FreeCAD.Vector(
        branch_start.x,
        branch_start.y,
        branch_start.z,
    )

    temporary_end = FreeCAD.Vector(
        branch_end.x
        + direction.x
        * extension,
        branch_end.y
        + direction.y
        * extension,
        branch_end.z
        + direction.z
        * extension,
    )

    keep_point = FreeCAD.Vector(
        branch_start.x,
        branch_start.y,
        branch_start.z,
    )

    return (
        temporary_start,
        temporary_end,
        keep_point,
    )


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


def primary_cope_component(
    shape,
    keep_point,
):
    """
    Return the cut component attached to the real branch tube.

    Temporary stock can leave a disconnected fragment on the
    far side of the through tube. That fragment is not part of
    the fabricated member and must be discarded.
    """

    solids = list(
        getattr(
            shape,
            "Solids",
            [],
        )
    )

    if len(
        solids
    ) <= 1:
        return shape

    def distance_to_keep_side(
        solid,
    ):
        center = (
            solid.CenterOfMass
        )

        return (
            (
                center.x
                - keep_point.x
            ) ** 2
            + (
                center.y
                - keep_point.y
            ) ** 2
            + (
                center.z
                - keep_point.z
            ) ** 2
        )

    return min(
        solids,
        key=distance_to_keep_side,
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
    Build a true tube fishmouth against a target tube.

    The ForgeCAD member itself keeps its design endpoint.

    During Boolean generation only, temporary branch stock is
    added beyond the joint so the complete fishmouth can form.
    After the target cylinder is subtracted, disconnected stock
    on the far side of the target tube is discarded.

    This keeps Member Through behavior correct:

        selected through tube -> real extension
        coped tube            -> no real extension
        cope geometry         -> temporary Boolean stock only
    """

    (
        temporary_start,
        temporary_end,
        keep_point,
    ) = temporary_branch_endpoints_for_cope(
        branch_start,
        branch_end,
        branch_profile,
        through_start,
        through_end,
        through_outside_diameter,
    )

    branch_shape, branch_length = (
        plain_shape_builder(
            temporary_start,
            temporary_end,
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

    cut_shape = branch_shape.cut(
        cutter
    )

    coped_shape = (
        primary_cope_component(
            cut_shape,
            keep_point,
        )
    )

    return (
        coped_shape,
        branch_length,
    )
