"""FreeCAD geometry helpers for ForgeCAD tube miters."""

import FreeCAD
import Part


def vector_between(
    start,
    end,
):
    """Return the vector from start to end."""

    return FreeCAD.Vector(
        end.x - start.x,
        end.y - start.y,
        end.z - start.z,
    )


def unit_vector(
    vector,
):
    """Return a normalized FreeCAD vector."""

    length = vector.Length

    if length <= 0:
        raise ValueError(
            "Cannot normalize a zero-length vector."
        )

    return FreeCAD.Vector(
        vector.x / length,
        vector.y / length,
        vector.z / length,
    )


def miter_plane_normal(
    joint_point,
    member_other_point,
    other_member_other_point,
):
    """
    Return the normal of the equal-angle miter plane.

    Both vectors point away from the common joint. Their sum
    is the internal angle bisector. The miter plane normal is
    parallel to that bisector.
    """

    first_direction = unit_vector(
        vector_between(
            joint_point,
            member_other_point,
        )
    )

    second_direction = unit_vector(
        vector_between(
            joint_point,
            other_member_other_point,
        )
    )

    bisector = FreeCAD.Vector(
        first_direction.x
        + second_direction.x,
        first_direction.y
        + second_direction.y,
        first_direction.z
        + second_direction.z,
    )

    if bisector.Length <= 1e-9:
        raise ValueError(
            "Cannot build a miter plane for "
            "opposite collinear members."
        )

    return unit_vector(
        bisector
    )


def point_dot(
    point,
    origin,
    normal,
):
    """Return signed point distance numerator from a plane."""

    return (
        (point.x - origin.x)
        * normal.x
        + (point.y - origin.y)
        * normal.y
        + (point.z - origin.z)
        * normal.z
    )


def build_half_space_cutter(
    plane_point,
    plane_normal,
    keep_point,
    size,
):
    """
    Build a large solid on the side of the plane to remove.

    keep_point identifies which side of the miter plane must
    remain as part of the tube.
    """

    size = float(
        size
    )

    if size <= 0:
        raise ValueError(
            "Miter cutter size must be greater than zero."
        )

    normal = unit_vector(
        plane_normal
    )

    keep_side = point_dot(
        keep_point,
        plane_point,
        normal,
    )

    if abs(
        keep_side
    ) <= 1e-9:
        raise ValueError(
            "Miter keep point cannot lie on the miter plane."
        )

    if keep_side > 0:
        cutter_direction = FreeCAD.Vector(
            -normal.x,
            -normal.y,
            -normal.z,
        )
    else:
        cutter_direction = FreeCAD.Vector(
            normal.x,
            normal.y,
            normal.z,
        )

    reference = FreeCAD.Vector(
        1,
        0,
        0,
    )

    if abs(
        normal.x
    ) > 0.9:
        reference = FreeCAD.Vector(
            0,
            1,
            0,
        )

    axis_u = normal.cross(
        reference
    )

    axis_u = unit_vector(
        axis_u
    )

    axis_v = normal.cross(
        axis_u
    )

    axis_v = unit_vector(
        axis_v
    )

    corner = FreeCAD.Vector(
        plane_point.x
        - axis_u.x * size
        - axis_v.x * size,
        plane_point.y
        - axis_u.y * size
        - axis_v.y * size,
        plane_point.z
        - axis_u.z * size
        - axis_v.z * size,
    )

    face = Part.Face(
        Part.makePolygon(
            [
                corner,
                FreeCAD.Vector(
                    corner.x
                    + axis_u.x * size * 2.0,
                    corner.y
                    + axis_u.y * size * 2.0,
                    corner.z
                    + axis_u.z * size * 2.0,
                ),
                FreeCAD.Vector(
                    corner.x
                    + axis_u.x * size * 2.0
                    + axis_v.x * size * 2.0,
                    corner.y
                    + axis_u.y * size * 2.0
                    + axis_v.y * size * 2.0,
                    corner.z
                    + axis_u.z * size * 2.0
                    + axis_v.z * size * 2.0,
                ),
                FreeCAD.Vector(
                    corner.x
                    + axis_v.x * size * 2.0,
                    corner.y
                    + axis_v.y * size * 2.0,
                    corner.z
                    + axis_v.z * size * 2.0,
                ),
                corner,
            ]
        )
    )

    return face.extrude(
        FreeCAD.Vector(
            cutter_direction.x * size * 2.0,
            cutter_direction.y * size * 2.0,
            cutter_direction.z * size * 2.0,
        )
    )


def miter_tube_shape(
    tube_shape,
    plane_point,
    plane_normal,
    keep_point,
    cutter_size,
):
    """Trim a tube to one side of a miter plane."""

    cutter = build_half_space_cutter(
        plane_point,
        plane_normal,
        keep_point,
        cutter_size,
    )

    return tube_shape.cut(
        cutter
    )
