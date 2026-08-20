"""Tests for ForgeCAD physical bent-tube paths."""

import math

import pytest

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
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


def test_single_bend_tube_has_two_straight_runs():
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

    assert tube.bend_count == 1
    assert len(tube.straight_runs) == 2


def test_developed_length_includes_straights_and_bend_arcs():
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

    expected = (
        500.0
        + 750.0
        + math.pi * 50.0
    )

    assert tube.developed_length == pytest.approx(
        expected
    )


def test_multiple_bends_accumulate_developed_length():
    tube = BentTube(
        straight_runs=(
            StraightRun(400.0),
            StraightRun(600.0),
            StraightRun(800.0),
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

    expected = (
        400.0
        + 600.0
        + 800.0
        + 100.0 * math.pi / 2.0
        + 150.0 * math.pi / 4.0
    )

    assert tube.developed_length == pytest.approx(
        expected
    )


def test_straight_tube_is_valid_with_no_bends():
    tube = BentTube(
        straight_runs=(
            StraightRun(1000.0),
        ),
        bends=(),
        profile=_profile(),
        material=_material(),
    )

    assert tube.bend_count == 0
    assert tube.developed_length == pytest.approx(
        1000.0
    )


def test_bent_tube_weight_uses_developed_length():
    tube = BentTube(
        straight_runs=(
            StraightRun(500.0),
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

    expected_volume_m3 = (
        tube.profile.cross_sectional_area
        * tube.developed_length
        / 1_000_000_000.0
    )

    assert tube.weight_kg == pytest.approx(
        expected_volume_m3
        * tube.material.density
    )


def test_bent_tube_requires_one_more_run_than_bend():
    with pytest.raises(
        ValueError,
        match="one more straight run",
    ):
        BentTube(
            straight_runs=(
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


def test_straight_run_rejects_negative_length():
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        StraightRun(
            -1.0
        )
