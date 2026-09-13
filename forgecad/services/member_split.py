"""Geometry helpers for splitting ForgeCAD straight members."""

import math

from forgecad.fabrication import (
    Member,
    Node,
)


DEFAULT_SPLIT_TOLERANCE = 1e-6


def point_distance(
    first,
    second,
) -> float:
    """Return the 3D distance between two point-like objects."""

    return math.sqrt(
        (
            float(first.x)
            - float(second.x)
        )
        ** 2
        + (
            float(first.y)
            - float(second.y)
        )
        ** 2
        + (
            float(first.z)
            - float(second.z)
        )
        ** 2
    )


def projected_point_on_member(
    member: Member,
    point,
) -> Node:
    """
    Return the orthogonal projection of a point onto a member centerline.

    The member is treated as an infinite line for the projection itself.
    """

    start = member.start
    end = member.end

    dx = (
        float(end.x)
        - float(start.x)
    )

    dy = (
        float(end.y)
        - float(start.y)
    )

    dz = (
        float(end.z)
        - float(start.z)
    )

    length_squared = (
        dx * dx
        + dy * dy
        + dz * dz
    )

    if length_squared <= (
        DEFAULT_SPLIT_TOLERANCE
        * DEFAULT_SPLIT_TOLERANCE
    ):
        raise ValueError(
            "Cannot split a zero-length member."
        )

    px = (
        float(point.x)
        - float(start.x)
    )

    py = (
        float(point.y)
        - float(start.y)
    )

    pz = (
        float(point.z)
        - float(start.z)
    )

    fraction = (
        (
            px * dx
            + py * dy
            + pz * dz
        )
        / length_squared
    )

    return Node(
        float(start.x)
        + fraction * dx,
        float(start.y)
        + fraction * dy,
        float(start.z)
        + fraction * dz,
    )


def split_fraction(
    member: Member,
    point,
) -> float:
    """Return the normalized location of a point along the member."""

    start = member.start
    end = member.end

    dx = (
        float(end.x)
        - float(start.x)
    )

    dy = (
        float(end.y)
        - float(start.y)
    )

    dz = (
        float(end.z)
        - float(start.z)
    )

    length_squared = (
        dx * dx
        + dy * dy
        + dz * dz
    )

    if length_squared <= (
        DEFAULT_SPLIT_TOLERANCE
        * DEFAULT_SPLIT_TOLERANCE
    ):
        raise ValueError(
            "Cannot split a zero-length member."
        )

    return (
        (
            (
                float(point.x)
                - float(start.x)
            )
            * dx
            + (
                float(point.y)
                - float(start.y)
            )
            * dy
            + (
                float(point.z)
                - float(start.z)
            )
            * dz
        )
        / length_squared
    )


def validate_split_point(
    member: Member,
    point,
    tolerance=DEFAULT_SPLIT_TOLERANCE,
) -> Node:
    """
    Validate and canonicalize a requested split location.

    The requested point must lie on the finite member centerline and
    must not coincide with either endpoint.
    """

    projected = (
        projected_point_on_member(
            member,
            point,
        )
    )

    if (
        point_distance(
            point,
            projected,
        )
        > float(
            tolerance
        )
    ):
        raise ValueError(
            "Split point must lie on the member centerline."
        )

    fraction = split_fraction(
        member,
        projected,
    )

    if (
        fraction
        <= float(
            tolerance
        )
        or fraction
        >= (
            1.0
            - float(
                tolerance
            )
        )
    ):
        raise ValueError(
            "Split point must lie inside the member, not at an endpoint."
        )

    return projected


def split_member(
    member: Member,
    point,
    tolerance=DEFAULT_SPLIT_TOLERANCE,
):
    """
    Split one straight member into two members.

    Profile and material are preserved. The returned members share the
    same canonical split node.
    """

    split_node = (
        validate_split_point(
            member,
            point,
            tolerance=tolerance,
        )
    )

    first = Member(
        start=member.start,
        end=split_node,
        profile=member.profile,
        material=member.material,
    )

    second = Member(
        start=split_node,
        end=member.end,
        profile=member.profile,
        material=member.material,
    )

    return (
        first,
        second,
    )
