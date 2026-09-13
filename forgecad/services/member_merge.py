"""Geometry helpers for safely merging collinear ForgeCAD members."""

import math

from forgecad.fabrication import (
    Member,
    Node,
)


DEFAULT_MERGE_TOLERANCE = 1e-5


def node_distance(
    first,
    second,
):
    """Return the 3D distance between two nodes."""

    dx = float(first.x) - float(second.x)
    dy = float(first.y) - float(second.y)
    dz = float(first.z) - float(second.z)

    return math.sqrt(
        dx * dx
        + dy * dy
        + dz * dz
    )


def nodes_match(
    first,
    second,
    tolerance=DEFAULT_MERGE_TOLERANCE,
):
    """Return True when two nodes occupy the same point."""

    return (
        node_distance(
            first,
            second,
        )
        <= float(
            tolerance
        )
    )


def shared_endpoint_and_outer_endpoints(
    first,
    second,
    tolerance=DEFAULT_MERGE_TOLERANCE,
):
    """
    Return shared endpoint and the two outer endpoints.

    None is returned unless the members share exactly one endpoint.
    """

    combinations = (
        (
            first.start,
            second.start,
            first.end,
            second.end,
        ),
        (
            first.start,
            second.end,
            first.end,
            second.start,
        ),
        (
            first.end,
            second.start,
            first.start,
            second.end,
        ),
        (
            first.end,
            second.end,
            first.start,
            second.start,
        ),
    )

    matches = []

    for (
        first_shared,
        second_shared,
        first_outer,
        second_outer,
    ) in combinations:
        if nodes_match(
            first_shared,
            second_shared,
            tolerance=tolerance,
        ):
            matches.append(
                (
                    first_shared,
                    first_outer,
                    second_outer,
                )
            )

    if len(matches) != 1:
        return None

    return matches[
        0
    ]


def endpoints_are_collinear_through_shared(
    shared,
    first_outer,
    second_outer,
    tolerance=DEFAULT_MERGE_TOLERANCE,
):
    """
    Return True when outer endpoints lie on opposite sides of shared point.

    The tolerance is applied to the normalized cross-product magnitude,
    which makes the comparison effectively angular and independent of
    member length.
    """

    ax = float(first_outer.x) - float(shared.x)
    ay = float(first_outer.y) - float(shared.y)
    az = float(first_outer.z) - float(shared.z)

    bx = float(second_outer.x) - float(shared.x)
    by = float(second_outer.y) - float(shared.y)
    bz = float(second_outer.z) - float(shared.z)

    a_length = math.sqrt(
        ax * ax
        + ay * ay
        + az * az
    )

    b_length = math.sqrt(
        bx * bx
        + by * by
        + bz * bz
    )

    if (
        a_length <= tolerance
        or b_length <= tolerance
    ):
        return False

    cross_x = ay * bz - az * by
    cross_y = az * bx - ax * bz
    cross_z = ax * by - ay * bx

    cross_length = math.sqrt(
        cross_x * cross_x
        + cross_y * cross_y
        + cross_z * cross_z
    )

    normalized_cross = (
        cross_length
        / (
            a_length
            * b_length
        )
    )

    if (
        normalized_cross
        > float(
            tolerance
        )
    ):
        return False

    dot = (
        ax * bx
        + ay * by
        + az * bz
    )

    return dot < 0.0


def merge_collinear_members(
    first,
    second,
    tolerance=DEFAULT_MERGE_TOLERANCE,
):
    """
    Return one continuous Member when two members form a straight tube.

    None is returned when they do not share one endpoint or are not
    collinear through that endpoint.
    """

    endpoints = (
        shared_endpoint_and_outer_endpoints(
            first,
            second,
            tolerance=tolerance,
        )
    )

    if endpoints is None:
        return None

    (
        shared,
        first_outer,
        second_outer,
    ) = endpoints

    if not endpoints_are_collinear_through_shared(
        shared,
        first_outer,
        second_outer,
        tolerance=tolerance,
    ):
        return None

    if first.profile != second.profile:
        return None

    if first.material != second.material:
        return None

    return Member(
        start=first_outer,
        end=second_outer,
        profile=first.profile,
        material=first.material,
    )
