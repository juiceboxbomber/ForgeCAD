"""Tests for true 3D ForgeCAD bent-tube centerlines."""

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
    Vector3D,
)
from forgecad.services.bent_tube_path import (
    CircularArcPathSegment,
    StraightPathSegment,
    build_bent_tube_centerline,
)


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


def test_single_90_degree_bend_constructs_tangent_xy_path():
    tube = BentTube(
        straight_runs=(
            StraightRun(500.0),
            StraightRun(750.0),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )

    path = build_bent_tube_centerline(
        tube
    )

    assert path.segment_count == 3

    first = path.segments[0]
    arc = path.segments[1]
    last = path.segments[2]

    assert isinstance(
        first,
        StraightPathSegment,
    )
    assert isinstance(
        arc,
        CircularArcPathSegment,
    )
    assert isinstance(
        last,
        StraightPathSegment,
    )

    assert first.end == Point3D(
        500.0,
        0.0,
        0.0,
    )

    assert arc.center == Point3D(
        500.0,
        100.0,
        0.0,
    )

    assert arc.end.x == pytest.approx(
        600.0
    )
    assert arc.end.y == pytest.approx(
        100.0
    )
    assert arc.end.z == pytest.approx(
        0.0
    )

    assert path.end_point.x == pytest.approx(
        600.0
    )
    assert path.end_point.y == pytest.approx(
        850.0
    )
    assert path.end_point.z == pytest.approx(
        0.0
    )


def test_second_bend_can_clock_out_of_first_bend_plane():
    tube = BentTube(
        straight_runs=(
            StraightRun(500.0),
            StraightRun(500.0),
            StraightRun(500.0),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
                rotation_degrees=0.0,
            ),
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
                rotation_degrees=90.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )

    path = build_bent_tube_centerline(
        tube
    )

    second_arc = path.segments[
        3
    ]

    assert isinstance(
        second_arc,
        CircularArcPathSegment,
    )

    # The first bend turns +X into +Y in the XY plane.
    # Clocking the second bend plane 90 degrees around +Y
    # moves the second bend out of that plane.
    assert abs(
        second_arc.end.z
    ) > 1.0

    assert abs(
        path.end_direction.z
    ) == pytest.approx(
        1.0,
        abs=1e-9,
    )


def test_centerline_honors_custom_start_and_direction():
    tube = BentTube(
        straight_runs=(
            StraightRun(100.0),
        ),
        bends=(),
        profile=_profile(),
        material=_material(),
    )

    path = build_bent_tube_centerline(
        tube,
        start_point=Point3D(
            10.0,
            20.0,
            30.0,
        ),
        initial_direction=Vector3D(
            0.0,
            1.0,
            0.0,
        ),
    )

    assert path.end_point == Point3D(
        10.0,
        120.0,
        30.0,
    )


def test_initial_bend_normal_cannot_parallel_tube_direction():
    tube = BentTube(
        straight_runs=(
            StraightRun(100.0),
        ),
        bends=(),
        profile=_profile(),
        material=_material(),
    )

    with pytest.raises(
        ValueError,
        match="cannot be parallel",
    ):
        build_bent_tube_centerline(
            tube,
            initial_direction=Vector3D(
                1.0,
                0.0,
                0.0,
            ),
            initial_bend_normal=Vector3D(
                1.0,
                0.0,
                0.0,
            ),
        )
