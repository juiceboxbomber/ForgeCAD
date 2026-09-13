"""Joint constraint geometry helpers."""

from forgecad.fabrication.joint_constraint import (
    CollinearThroughConstraint,
)
from forgecad.geometry.point import Point3D
from forgecad.services.joint_member_roles import (
    identify_member_roles,
)


def vector_between(
    start,
    end,
):
    return (
        float(
            end.x - start.x
        ),
        float(
            end.y - start.y
        ),
        float(
            end.z - start.z
        ),
    )


def dot_product(
    a,
    b,
):
    return (
        a[0] * b[0]
        + a[1] * b[1]
        + a[2] * b[2]
    )


def cross_product(
    a,
    b,
):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def squared_length(
    vector,
):
    return dot_product(
        vector,
        vector,
    )


def is_zero_vector(
    vector,
    tolerance=1e-9,
):
    return all(
        abs(
            component
        )
        <= tolerance
        for component
        in vector
    )


def members_are_collinear_through_joint(
    first_member,
    second_member,
    joint,
):
    """
    Return True when two members share a joint and lie on one axis.
    """

    if (
        first_member.start == joint
    ):
        first_outer = (
            first_member.end
        )

    elif (
        first_member.end == joint
    ):
        first_outer = (
            first_member.start
        )

    else:
        return False

    if (
        second_member.start == joint
    ):
        second_outer = (
            second_member.end
        )

    elif (
        second_member.end == joint
    ):
        second_outer = (
            second_member.start
        )

    else:
        return False

    first_direction = (
        vector_between(
            joint,
            first_outer,
        )
    )

    second_direction = (
        vector_between(
            joint,
            second_outer,
        )
    )

    if (
        is_zero_vector(
            first_direction
        )
        or is_zero_vector(
            second_direction
        )
    ):
        return False

    return is_zero_vector(
        cross_product(
            first_direction,
            second_direction,
        )
    )


def project_point_to_axis(
    point,
    axis_start,
    axis_end,
):
    """
    Return the orthogonal projection of a point onto an infinite axis.
    """

    axis = vector_between(
        axis_start,
        axis_end,
    )

    axis_length_squared = (
        squared_length(
            axis
        )
    )

    if (
        axis_length_squared
        <= 1e-18
    ):
        raise ValueError(
            "Cannot project onto a zero-length axis."
        )

    offset = vector_between(
        axis_start,
        point,
    )

    scale = (
        dot_product(
            offset,
            axis,
        )
        / axis_length_squared
    )

    return Point3D(
        x=(
            axis_start.x
            + axis[0] * scale
        ),
        y=(
            axis_start.y
            + axis[1] * scale
        ),
        z=(
            axis_start.z
            + axis[2] * scale
        ),
    )


def solve_collinear_through_joint(
    proposed_position,
    constraint,
):
    """
    Constrain a proposed joint position to the through-member axis.
    """

    return project_point_to_axis(
        proposed_position,
        constraint.axis_start,
        constraint.axis_end,
    )


def member_outer_node(
    member,
    joint_node,
):
    """Return the member endpoint opposite the joint."""

    if member.start == joint_node:
        return member.end

    if member.end == joint_node:
        return member.start

    return None


def collinear_through_constraint_for_joint(
    joint,
):
    """
    Return a collinear movement constraint for a through-member joint.

    A joint may be represented in either of two valid ways:

    - one continuous physical member passing through the joint interior;
    - two endpoint-connected members forming a split straight-through pair.

    In both cases, constrain movement to the through-member centerline.
    """

    roles = identify_member_roles(
        joint
    )

    if (
        len(
            roles.through_members
        )
        == 1
    ):
        through_member = (
            roles.through_members[
                0
            ]
        )

        return CollinearThroughConstraint(
            axis_start=Point3D(
                float(
                    through_member.start.x
                ),
                float(
                    through_member.start.y
                ),
                float(
                    through_member.start.z
                ),
            ),
            axis_end=Point3D(
                float(
                    through_member.end.x
                ),
                float(
                    through_member.end.y
                ),
                float(
                    through_member.end.z
                ),
            ),
        )

    if not roles.has_through_pair:
        return None

    first_member, second_member = (
        roles.through_members
    )

    first_outer = member_outer_node(
        first_member,
        joint.node,
    )

    second_outer = member_outer_node(
        second_member,
        joint.node,
    )

    if (
        first_outer is None
        or second_outer is None
    ):
        return None

    return CollinearThroughConstraint(
        axis_start=Point3D(
            float(first_outer.x),
            float(first_outer.y),
            float(first_outer.z),
        ),
        axis_end=Point3D(
            float(second_outer.x),
            float(second_outer.y),
            float(second_outer.z),
        ),
    )
