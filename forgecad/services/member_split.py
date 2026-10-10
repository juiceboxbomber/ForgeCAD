"""Geometry helpers for splitting ForgeCAD straight members."""

import math
from dataclasses import dataclass

from forgecad.fabrication import (
    BentTube,
    Member,
    Node,
    StraightRun,
)
from forgecad.geometry import Point3D
from forgecad.services.bent_tube_path import (
    StraightPathSegment,
    build_bent_tube_centerline,
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


@dataclass(frozen=True, slots=True)
class BentSplitLocation:
    point: Point3D
    straight_run_index: int
    fraction: float


def _project_point_on_straight_segment(segment, point):
    dx = float(segment.end.x) - float(segment.start.x)
    dy = float(segment.end.y) - float(segment.start.y)
    dz = float(segment.end.z) - float(segment.start.z)

    length_squared = dx * dx + dy * dy + dz * dz
    if length_squared <= DEFAULT_SPLIT_TOLERANCE ** 2:
        return None

    px = float(point.x) - float(segment.start.x)
    py = float(point.y) - float(segment.start.y)
    pz = float(point.z) - float(segment.start.z)

    fraction = (px * dx + py * dy + pz * dz) / length_squared
    clamped = max(0.0, min(1.0, fraction))

    projected = Point3D(
        float(segment.start.x) + clamped * dx,
        float(segment.start.y) + clamped * dy,
        float(segment.start.z) + clamped * dz,
    )

    return projected, clamped, point_distance(point, projected)


def bent_split_location(
    tube: BentTube,
    point,
    *,
    start_point=None,
    initial_direction=None,
    initial_bend_normal=None,
    tolerance=DEFAULT_SPLIT_TOLERANCE,
):
    if not isinstance(tube, BentTube):
        raise TypeError("tube must be a BentTube instance.")

    kwargs = {}
    if start_point is not None:
        kwargs["start_point"] = start_point
    if initial_direction is not None:
        kwargs["initial_direction"] = initial_direction
    if initial_bend_normal is not None:
        kwargs["initial_bend_normal"] = initial_bend_normal

    centerline = build_bent_tube_centerline(tube, **kwargs)

    candidates = []
    straight_run_index = 0

    for segment in centerline.segments:
        if not isinstance(segment, StraightPathSegment):
            continue

        projected = _project_point_on_straight_segment(segment, point)
        if projected is not None:
            projected_point, fraction, distance = projected
            candidates.append(
                (
                    distance,
                    straight_run_index,
                    fraction,
                    projected_point,
                )
            )

        straight_run_index += 1

    if not candidates:
        raise ValueError("Bent tube contains no splittable straight run.")

    distance, run_index, fraction, projected_point = min(
        candidates,
        key=lambda candidate: candidate[0],
    )

    tolerance = float(tolerance)

    if distance > tolerance:
        raise ValueError(
            "Split point must lie on a straight portion "
            "of the bent member centerline."
        )

    if fraction <= tolerance or fraction >= 1.0 - tolerance:
        raise ValueError(
            "Split point must lie inside a straight run, "
            "not at a bend tangent or member endpoint."
        )

    return BentSplitLocation(
        point=projected_point,
        straight_run_index=run_index,
        fraction=fraction,
    )


def split_bent_tube(
    tube: BentTube,
    point,
    *,
    start_point=None,
    initial_direction=None,
    initial_bend_normal=None,
    tolerance=DEFAULT_SPLIT_TOLERANCE,
):
    """
    Split one BentTube definition at an interior point of a straight run.

    The bend sequence is preserved exactly. The straight run containing the
    split is divided into two runs, one terminating the first tube and one
    starting the second tube.
    """

    location = bent_split_location(
        tube,
        point,
        start_point=start_point,
        initial_direction=initial_direction,
        initial_bend_normal=initial_bend_normal,
        tolerance=tolerance,
    )

    run_index = location.straight_run_index
    source_run = tube.straight_runs[
        run_index
    ]

    first_length = (
        source_run.length_mm
        * location.fraction
    )
    second_length = (
        source_run.length_mm
        - first_length
    )

    first_runs = (
        tuple(
            tube.straight_runs[
                :run_index
            ]
        )
        + (
            StraightRun(
                first_length
            ),
        )
    )

    second_runs = (
        (
            StraightRun(
                second_length
            ),
        )
        + tuple(
            tube.straight_runs[
                run_index + 1 :
            ]
        )
    )

    first = BentTube(
        straight_runs=first_runs,
        bends=tuple(
            tube.bends[
                :run_index
            ]
        ),
        profile=tube.profile,
        material=tube.material,
    )

    second = BentTube(
        straight_runs=second_runs,
        bends=tuple(
            tube.bends[
                run_index:
            ]
        ),
        profile=tube.profile,
        material=tube.material,
    )

    return (
        first,
        second,
        location,
    )
