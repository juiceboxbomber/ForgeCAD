"""Geometric regression tests for ForgeCAD bent-tube centerlines."""

import pytest

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import (
    Point3D,
)
from forgecad.services.bent_tube_path import (
    CircularArcPathSegment,
    StraightPathSegment,
    build_bent_tube_centerline,
)


TOLERANCE = 1e-9


def _material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def _profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def _distance(
    first: Point3D,
    second: Point3D,
) -> float:
    return first.vector_to(
        second
    ).magnitude


def _multi_bend_tube():
    return BentTube(
        straight_runs=(
            StraightRun(400.0),
            StraightRun(550.0),
            StraightRun(325.0),
        ),
        bends=(
            Bend(
                angle_degrees=60.0,
                centerline_radius=100.0,
                rotation_degrees=0.0,
            ),
            Bend(
                angle_degrees=75.0,
                centerline_radius=125.0,
                rotation_degrees=90.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


def test_adjacent_centerline_segments_share_exact_endpoints():
    path = build_bent_tube_centerline(
        _multi_bend_tube()
    )

    for first, second in zip(
        path.segments,
        path.segments[1:],
    ):
        assert first.end == second.start


def test_arc_start_and_end_are_exactly_one_clr_from_center():
    path = build_bent_tube_centerline(
        _multi_bend_tube()
    )

    arcs = tuple(
        segment
        for segment in path.segments
        if isinstance(
            segment,
            CircularArcPathSegment,
        )
    )

    for arc in arcs:
        assert _distance(
            arc.center,
            arc.start,
        ) == pytest.approx(
            arc.radius_mm,
            abs=TOLERANCE,
        )

        assert _distance(
            arc.center,
            arc.end,
        ) == pytest.approx(
            arc.radius_mm,
            abs=TOLERANCE,
        )


def test_straight_to_arc_connection_is_tangent():
    path = build_bent_tube_centerline(
        _multi_bend_tube()
    )

    for index, segment in enumerate(
        path.segments
    ):
        if not isinstance(
            segment,
            CircularArcPathSegment,
        ):
            continue

        previous = path.segments[
            index - 1
        ]

        assert isinstance(
            previous,
            StraightPathSegment,
        )

        incoming = (
            previous.start
            .vector_to(
                previous.end
            )
            .normalized()
        )

        start_radius = (
            segment.center
            .vector_to(
                segment.start
            )
            .normalized()
        )

        assert incoming.dot(
            start_radius
        ) == pytest.approx(
            0.0,
            abs=TOLERANCE,
        )


def test_arc_to_straight_connection_is_tangent():
    path = build_bent_tube_centerline(
        _multi_bend_tube()
    )

    for index, segment in enumerate(
        path.segments
    ):
        if not isinstance(
            segment,
            CircularArcPathSegment,
        ):
            continue

        following = path.segments[
            index + 1
        ]

        assert isinstance(
            following,
            StraightPathSegment,
        )

        outgoing = (
            following.start
            .vector_to(
                following.end
            )
            .normalized()
        )

        end_radius = (
            segment.center
            .vector_to(
                segment.end
            )
            .normalized()
        )

        assert outgoing.dot(
            end_radius
        ) == pytest.approx(
            0.0,
            abs=TOLERANCE,
        )


def test_straight_segment_lengths_match_bent_tube_runs():
    tube = _multi_bend_tube()

    path = build_bent_tube_centerline(
        tube
    )

    straights = tuple(
        segment
        for segment in path.segments
        if isinstance(
            segment,
            StraightPathSegment,
        )
    )

    assert len(
        straights
    ) == len(
        tube.straight_runs
    )

    for segment, run in zip(
        straights,
        tube.straight_runs,
    ):
        assert segment.length == pytest.approx(
            run.length_mm,
            abs=TOLERANCE,
        )


def test_centerline_total_length_matches_developed_length():
    tube = _multi_bend_tube()

    path = build_bent_tube_centerline(
        tube
    )

    total = 0.0

    for segment in path.segments:
        if isinstance(
            segment,
            StraightPathSegment,
        ):
            total += segment.length
        else:
            total += (
                segment.radius_mm
                * segment.angle_degrees
                * 3.141592653589793
                / 180.0
            )

    assert total == pytest.approx(
        tube.developed_length,
        abs=TOLERANCE,
    )


def test_three_dimensional_clocking_preserves_continuity_and_radius():
    tube = BentTube(
        straight_runs=(
            StraightRun(300.0),
            StraightRun(400.0),
            StraightRun(500.0),
            StraightRun(600.0),
        ),
        bends=(
            Bend(
                angle_degrees=45.0,
                centerline_radius=80.0,
                rotation_degrees=0.0,
            ),
            Bend(
                angle_degrees=60.0,
                centerline_radius=80.0,
                rotation_degrees=45.0,
            ),
            Bend(
                angle_degrees=30.0,
                centerline_radius=80.0,
                rotation_degrees=120.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )

    path = build_bent_tube_centerline(
        tube
    )

    assert abs(
        path.end_point.z
    ) > 1.0

    for first, second in zip(
        path.segments,
        path.segments[1:],
    ):
        assert first.end == second.start

    for segment in path.segments:
        if isinstance(
            segment,
            CircularArcPathSegment,
        ):
            assert _distance(
                segment.center,
                segment.start,
            ) == pytest.approx(
                80.0,
                abs=TOLERANCE,
            )
            assert _distance(
                segment.center,
                segment.end,
            ) == pytest.approx(
                80.0,
                abs=TOLERANCE,
            )
