"""Geometry services for trimming and extending ForgeCAD straight members."""

import math

from forgecad.fabrication import (
    BentMember,
    Member,
    Node,
)
from forgecad.geometry import (
    Point3D,
)
from forgecad.services.bent_tube_path import (
    build_bent_tube_centerline,
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


def _node_offset(
    node,
    direction,
    distance,
):
    """Return a Node offset along one normalized direction."""

    return Node(
        float(node.x)
        + float(direction.x)
        * float(distance),
        float(node.y)
        + float(direction.y)
        * float(distance),
        float(node.z)
        + float(direction.z)
        * float(distance),
    )


def bent_endpoint_intersection_3d(
    bent_member,
    target_member,
    endpoint,
    tolerance=DEFAULT_INTERSECTION_TOLERANCE,
):
    """
    Intersect one bent-member endpoint tangent with a straight target.

    The temporary source axis points OUTWARD from the chosen physical end.
    Its parameter therefore has direct meaning in millimeters:

        positive -> extend outward
        negative -> trim inward

    A trim may shorten only the straight run adjacent to the selected end.
    It may not reach or pass the nearest bend tangent point.
    """

    if not isinstance(
        bent_member,
        BentMember,
    ):
        raise TypeError(
            "Bent Trim/Extend requires a BentMember source."
        )

    if not isinstance(
        target_member,
        Member,
    ):
        raise ValueError(
            "Bent-member Trim/Extend currently requires a straight target."
        )

    requested = str(
        endpoint or ""
    ).strip().lower()

    if requested not in (
        "start",
        "end",
    ):
        raise ValueError(
            "Bent-member Trim/Extend requires choosing start or end."
        )

    centerline = build_bent_tube_centerline(
        bent_member.tube,
        start_point=Point3D(
            float(
                bent_member.start.x
            ),
            float(
                bent_member.start.y
            ),
            float(
                bent_member.start.z
            ),
        ),
        initial_direction=(
            bent_member.initial_direction
        ),
        initial_bend_normal=(
            bent_member.initial_bend_normal
        ),
    )

    if requested == "start":
        physical_endpoint = (
            bent_member.start
        )
        outward_direction = (
            bent_member
            .initial_direction
            .normalized()
            .scaled(
                -1.0
            )
        )
        adjacent_run_length = float(
            bent_member
            .tube
            .straight_runs[
                0
            ]
            .length_mm
        )
    else:
        physical_endpoint = (
            bent_member.end
        )
        outward_direction = (
            centerline
            .end_direction
            .normalized()
        )
        adjacent_run_length = float(
            bent_member
            .tube
            .straight_runs[
                -1
            ]
            .length_mm
        )

    tangent_axis = Member(
        start=physical_endpoint,
        end=_node_offset(
            physical_endpoint,
            outward_direction,
            1.0,
        ),
        profile=bent_member.profile,
        material=bent_member.material,
    )

    (
        intersection,
        signed_distance,
        target_parameter,
    ) = line_intersection_3d(
        tangent_axis,
        target_member,
        tolerance=tolerance,
    )

    signed_distance = float(
        signed_distance
    )
    tolerance = float(
        tolerance
    )

    if abs(
        signed_distance
    ) <= tolerance:
        kind = "none"

    elif signed_distance > 0.0:
        kind = "extend"

    else:
        trim_distance = -signed_distance

        if trim_distance >= (
            adjacent_run_length
            - tolerance
        ):
            raise ValueError(
                "Bent-member Trim would reach or pass the nearest bend."
            )

        kind = "trim"

    return (
        intersection,
        signed_distance,
        target_parameter,
        kind,
    )

def straight_to_bent_endpoint_intersection_3d(
    source_member,
    bent_target,
    target_endpoint,
    tolerance=DEFAULT_INTERSECTION_TOLERANCE,
):
    """Intersect a straight source with one true bent-target endpoint tangent."""

    if not isinstance(source_member, Member):
        raise TypeError(
            "Straight-to-bent Trim/Extend requires a straight source."
        )

    if not isinstance(bent_target, BentMember):
        raise TypeError(
            "Straight-to-bent Trim/Extend requires a bent target."
        )

    requested = str(target_endpoint or "").strip().lower()

    if requested not in ("start", "end"):
        raise ValueError(
            "Choose the start or end of the bent target."
        )

    centerline = build_bent_tube_centerline(
        bent_target.tube,
        start_point=Point3D(
            float(bent_target.start.x),
            float(bent_target.start.y),
            float(bent_target.start.z),
        ),
        initial_direction=bent_target.initial_direction,
        initial_bend_normal=bent_target.initial_bend_normal,
    )

    if requested == "start":
        physical_endpoint = bent_target.start
        tangent_direction = bent_target.initial_direction.normalized()
    else:
        physical_endpoint = bent_target.end
        tangent_direction = centerline.end_direction.normalized()

    tangent_member = Member(
        start=physical_endpoint,
        end=_node_offset(
            physical_endpoint,
            tangent_direction,
            1.0,
        ),
        profile=bent_target.profile,
        material=bent_target.material,
    )

    return line_intersection_3d(
        source_member,
        tangent_member,
        tolerance=tolerance,
    )

def bent_to_bent_endpoint_intersection_3d(
    source_member,
    target_member,
    source_endpoint,
    target_endpoint,
    tolerance=DEFAULT_INTERSECTION_TOLERANCE,
):
    """
    Intersect one physical endpoint tangent of a bent source with one physical
    endpoint tangent of a bent target.

    The source tangent points outward from the selected source endpoint so the
    returned source parameter is positive for extension and negative for trim.
    The bent start-to-end chord is never used.
    """

    if not isinstance(
        source_member,
        BentMember,
    ):
        raise TypeError(
            "Bent-to-bent Trim/Extend requires a bent source."
        )

    if not isinstance(
        target_member,
        BentMember,
    ):
        raise TypeError(
            "Bent-to-bent Trim/Extend requires a bent target."
        )

    source_requested = str(
        source_endpoint or ""
    ).strip().lower()

    target_requested = str(
        target_endpoint or ""
    ).strip().lower()

    if source_requested not in (
        "start",
        "end",
    ):
        raise ValueError(
            "Choose the start or end of the bent source."
        )

    if target_requested not in (
        "start",
        "end",
    ):
        raise ValueError(
            "Choose the start or end of the bent target."
        )

    source_centerline = build_bent_tube_centerline(
        source_member.tube,
        start_point=Point3D(
            float(
                source_member.start.x
            ),
            float(
                source_member.start.y
            ),
            float(
                source_member.start.z
            ),
        ),
        initial_direction=(
            source_member.initial_direction
        ),
        initial_bend_normal=(
            source_member.initial_bend_normal
        ),
    )

    target_centerline = build_bent_tube_centerline(
        target_member.tube,
        start_point=Point3D(
            float(
                target_member.start.x
            ),
            float(
                target_member.start.y
            ),
            float(
                target_member.start.z
            ),
        ),
        initial_direction=(
            target_member.initial_direction
        ),
        initial_bend_normal=(
            target_member.initial_bend_normal
        ),
    )

    if source_requested == "start":
        source_point = (
            source_member.start
        )
        source_outward = (
            source_member
            .initial_direction
            .normalized()
            .scaled(
                -1.0
            )
        )
        adjacent_run_length = float(
            source_member
            .tube
            .straight_runs[
                0
            ]
            .length_mm
        )
    else:
        source_point = (
            source_member.end
        )
        source_outward = (
            source_centerline
            .end_direction
            .normalized()
        )
        adjacent_run_length = float(
            source_member
            .tube
            .straight_runs[
                -1
            ]
            .length_mm
        )

    if target_requested == "start":
        target_point = (
            target_member.start
        )
        target_direction = (
            target_member
            .initial_direction
            .normalized()
        )
    else:
        target_point = (
            target_member.end
        )
        target_direction = (
            target_centerline
            .end_direction
            .normalized()
        )

    source_axis = Member(
        start=source_point,
        end=_node_offset(
            source_point,
            source_outward,
            1.0,
        ),
        profile=source_member.profile,
        material=source_member.material,
    )

    target_axis = Member(
        start=target_point,
        end=_node_offset(
            target_point,
            target_direction,
            1.0,
        ),
        profile=target_member.profile,
        material=target_member.material,
    )

    (
        intersection,
        source_parameter,
        target_parameter,
    ) = line_intersection_3d(
        source_axis,
        target_axis,
        tolerance=tolerance,
    )

    source_parameter = float(
        source_parameter
    )
    tolerance = float(
        tolerance
    )

    if abs(
        source_parameter
    ) <= tolerance:
        kind = "none"

    elif source_parameter > 0.0:
        kind = "extend"

    else:
        trim_distance = -source_parameter

        if trim_distance >= (
            adjacent_run_length
            - tolerance
        ):
            raise ValueError(
                "Bent-member Trim would reach or pass the nearest bend."
            )

        kind = "trim"

    return (
        intersection,
        source_parameter,
        target_parameter,
        kind,
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
