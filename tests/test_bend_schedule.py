"""Tests for ForgeCAD bend schedules."""

import math

import pytest

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.services.bend_schedule import (
    build_bend_schedule,
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


def test_single_bend_schedule_uses_first_tangent_position():
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

    schedule = build_bend_schedule(
        tube
    )

    assert schedule.bend_count == 1

    item = schedule.items[0]

    assert item.bend_number == 1
    assert item.start_position_mm == pytest.approx(
        500.0
    )
    assert item.angle_degrees == pytest.approx(
        90.0
    )
    assert item.centerline_radius_mm == pytest.approx(
        100.0
    )
    assert item.rotation_degrees == pytest.approx(
        0.0
    )
    assert item.arc_length_mm == pytest.approx(
        math.pi * 50.0
    )


def test_second_bend_position_includes_first_bend_arc():
    tube = BentTube(
        straight_runs=(
            StraightRun(500.0),
            StraightRun(600.0),
            StraightRun(700.0),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
            Bend(
                angle_degrees=45.0,
                centerline_radius=150.0,
                rotation_degrees=90.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )

    schedule = build_bend_schedule(
        tube
    )

    first_arc = (
        100.0
        * math.pi
        / 2.0
    )

    assert (
        schedule.items[1].start_position_mm
        == pytest.approx(
            500.0
            + first_arc
            + 600.0
        )
    )


def test_schedule_preserves_bend_order_and_rotation():
    tube = BentTube(
        straight_runs=(
            StraightRun(100.0),
            StraightRun(200.0),
            StraightRun(300.0),
        ),
        bends=(
            Bend(
                angle_degrees=30.0,
                centerline_radius=75.0,
                rotation_degrees=15.0,
            ),
            Bend(
                angle_degrees=60.0,
                centerline_radius=125.0,
                rotation_degrees=270.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )

    schedule = build_bend_schedule(
        tube
    )

    assert [
        item.bend_number
        for item in schedule.items
    ] == [
        1,
        2,
    ]

    assert [
        item.rotation_degrees
        for item in schedule.items
    ] == [
        15.0,
        270.0,
    ]


def test_schedule_reports_complete_developed_length():
    tube = BentTube(
        straight_runs=(
            StraightRun(400.0),
            StraightRun(500.0),
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

    schedule = build_bend_schedule(
        tube
    )

    assert (
        schedule.developed_length_mm
        == pytest.approx(
            tube.developed_length
        )
    )


def test_straight_tube_has_empty_bend_schedule():
    tube = BentTube(
        straight_runs=(
            StraightRun(1000.0),
        ),
        bends=(),
        profile=_profile(),
        material=_material(),
    )

    schedule = build_bend_schedule(
        tube
    )

    assert schedule.items == ()
    assert schedule.bend_count == 0
    assert (
        schedule.developed_length_mm
        == pytest.approx(1000.0)
    )


def test_build_bend_schedule_rejects_wrong_type():
    with pytest.raises(
        TypeError,
        match="BentTube",
    ):
        build_bend_schedule(
            object()
        )
