"""Geometry services for trimming and extending ForgeCAD straight members."""

import math

from forgecad.fabrication import (
    Member,
    Node,
)


DEFAULT_INTERSECTION_TOLERANCE = 1e-6


def _vector(
    start,
    end,
):
    """Return the vector from start to end."""

    return (
        float(end.x)
        - float(start.x),
        float(end.y)
        - float(start.y),
        float(end.z)
        - float(start.z),
    )


def _subtract(
    first,
    second,
):
    """Return first - second for point/vector-like triples."""

    return (
        float(first[0])
        - float(second[0]),
        float(first[1])
        - float(second[1]),
        float(first[2])
        - float(second[2]),
    )


def _dot(
    first,
    second,
):
    """Return the 3D dot product."""

    return (
        first[0] * second[0]
        + first[1] * second[1]
        + first[2] * second[2]
    )


def _cross(
    first,
    second,
):
    """Return the 3D cross product."""

    return (
        first[1] * second[2]
        - first[2] * second[1],
        first[2] * second[0]
        - first[0] * second[2],
        first[0] * second[1]
        - first[1] * second[0],
    )


def _length(
    vector,
):
    """Return the Euclidean length of a 3D vector."""

    return math.sqrt(
        _dot(
            vector,
            vector,
        )
    )


def _point_tuple(
    point,
):
    """Return point coordinates as floats."""

    return (
        float(point.x),
        float(point.y),
        float(point.z),
    )


def line_intersection_3d(
    first_member,
    second_member,
    tolerance=DEFAULT_INTERSECTION_TOLERANCE,
):
    """
    Return the true 3D intersection of two infinite member centerlines.

    The result is:

        intersection_node, first_parameter, second_parameter

    Parameter 0 is the start point and parameter 1 is the end point of
    the corresponding finite member.

    Parallel, collinear, skew, and degenerate lines are rejected.
    """

    tolerance = float(
        tolerance
    )

    first_direction = _vector(
        first_member.start,
        first_member.end,
    )

    second_direction = _vector(
        second_member.start,
        second_member.end,
    )

    first_length = _length(
        first_direction
    )

    second_length = _length(
        second_direction
    )

    if (
        first_length
        <= tolerance
        or second_length
        <= tolerance
    ):
        raise ValueError(
            "Trim/Extend requires non-zero-length members."
        )

    cross_direction = _cross(
        first_direction,
        second_direction,
    )

    cross_length = _length(
        cross_direction
    )

    parallel_threshold = (
        tolerance
        * first_length
        * second_length
    )

    start_delta = _subtract(
        _point_tuple(
            second_member.start
        ),
        _point_tuple(
            first_member.start
        ),
    )

    if cross_length <= parallel_threshold:
        collinear_measure = _length(
            _cross(
                start_delta,
                first_direction,
            )
        )

        collinear_threshold = (
            tolerance
            * first_length
        )

        if (
            collinear_measure
            <= collinear_threshold
        ):
            raise ValueError(
                "Collinear members have no unique Trim/Extend intersection."
            )

        raise ValueError(
            "Parallel members do not intersect."
        )

    cross_squared = _dot(
        cross_direction,
        cross_direction,
    )

    first_parameter = (
        _dot(
            _cross(
                start_delta,
                second_direction,
            ),
            cross_direction,
        )
        / cross_squared
    )

    second_parameter = (
        _dot(
            _cross(
                start_delta,
                first_direction,
            ),
            cross_direction,
        )
        / cross_squared
    )

    first_point = (
        _point_tuple(
            first_member.start
        )[
            0
        ]
        + first_parameter
        * first_direction[
            0
        ],
        _point_tuple(
            first_member.start
        )[
            1
        ]
        + first_parameter
        * first_direction[
            1
        ],
        _point_tuple(
            first_member.start
        )[
            2
        ]
        + first_parameter
        * first_direction[
            2
        ],
    )

    second_point = (
        _point_tuple(
            second_member.start
        )[
            0
        ]
        + second_parameter
        * second_direction[
            0
        ],
        _point_tuple(
            second_member.start
        )[
            1
        ]
        + second_parameter
        * second_direction[
            1
        ],
        _point_tuple(
            second_member.start
        )[
            2
        ]
        + second_parameter
        * second_direction[
            2
        ],
    )

    separation = _length(
        _subtract(
            first_point,
            second_point,
        )
    )

    if separation > tolerance:
        raise ValueError(
            "Member centerlines do not intersect in 3D."
        )

    intersection = Node(
        (
            first_point[
                0
            ]
            + second_point[
                0
            ]
        )
        * 0.5,
        (
            first_point[
                1
            ]
            + second_point[
                1
            ]
        )
        * 0.5,
        (
            first_point[
                2
            ]
            + second_point[
                2
            ]
        )
        * 0.5,
    )

    return (
        intersection,
        first_parameter,
        second_parameter,
    )


def classify_parameter(
    parameter,
    tolerance=DEFAULT_INTERSECTION_TOLERANCE,
):
    """
    Classify a line parameter relative to a finite member.

    Returns one of:

        before_start
        at_start
        inside
        at_end
        beyond_end
    """

    parameter = float(
        parameter
    )

    tolerance = float(
        tolerance
    )

    if parameter < -tolerance:
        return "before_start"

    if abs(
        parameter
    ) <= tolerance:
        return "at_start"

    if parameter > (
        1.0
        + tolerance
    ):
        return "beyond_end"

    if abs(
        parameter
        - 1.0
    ) <= tolerance:
        return "at_end"

    return "inside"


def modification_kind(
    parameter,
    tolerance=DEFAULT_INTERSECTION_TOLERANCE,
):
    """
    Return the natural operation implied by an intersection parameter.

    An interior intersection requires trimming. An intersection outside
    the finite member requires extending. Existing endpoints require no
    geometric modification.
    """

    classification = (
        classify_parameter(
            parameter,
            tolerance=tolerance,
        )
    )

    if classification == "inside":
        return "trim"

    if classification in (
        "before_start",
        "beyond_end",
    ):
        return "extend"

    return "none"


def replace_member_endpoint(
    member,
    intersection,
    endpoint,
):
    """
    Return a copy of a member with one endpoint moved to intersection.

    endpoint must be "start" or "end". Profile and material are preserved.
    """

    endpoint = str(
        endpoint
    ).strip().lower()

    if endpoint not in (
        "start",
        "end",
    ):
        raise ValueError(
            "Endpoint must be 'start' or 'end'."
        )

    if endpoint == "start":
        start = intersection
        end = member.end

    else:
        start = member.start
        end = intersection

    if start == end:
        raise ValueError(
            "Trim/Extend would create a zero-length member."
        )

    return Member(
        start=start,
        end=end,
        profile=member.profile,
        material=member.material,
    )
