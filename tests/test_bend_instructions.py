"""Tests for ForgeCAD fabrication bend instructions."""

import math

import pytest

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.services.bend_instructions import (
    BendMarkReference,
    build_bend_instructions,
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


def _tube():
    return BentTube(
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


def test_start_tangent_marks_match_geometric_schedule():
    instructions = build_bend_instructions(
        _tube()
    )

    first_arc = (
        100.0
        * math.pi
        / 2.0
    )

    assert (
        instructions.items[0].mark_position_mm
        == pytest.approx(500.0)
    )

    assert (
        instructions.items[1].mark_position_mm
        == pytest.approx(
            500.0
            + first_arc
            + 600.0
        )
    )


def test_center_of_bend_marks_are_half_arc_after_start_tangent():
    instructions = build_bend_instructions(
        _tube(),
        mark_reference=(
            BendMarkReference.CENTER_OF_BEND
        ),
    )

    first_arc = (
        100.0
        * math.pi
        / 2.0
    )

    assert (
        instructions.items[0].mark_position_mm
        == pytest.approx(
            500.0
            + first_arc / 2.0
        )
    )


def test_instruction_preserves_bend_geometry_and_rotation():
    instructions = build_bend_instructions(
        _tube()
    )

    second = instructions.items[1]

    assert second.bend_number == 2
    assert second.angle_degrees == pytest.approx(
        45.0
    )
    assert (
        second.centerline_radius_mm
        == pytest.approx(150.0)
    )
    assert second.rotation_degrees == pytest.approx(
        90.0
    )


def test_instruction_cut_length_is_developed_tube_length():
    tube = _tube()

    instructions = build_bend_instructions(
        tube
    )

    assert (
        instructions.cut_length_mm
        == pytest.approx(
            tube.developed_length
        )
    )


def test_straight_tube_produces_no_bend_marks():
    tube = BentTube(
        straight_runs=(
            StraightRun(1000.0),
        ),
        bends=(),
        profile=_profile(),
        material=_material(),
    )

    instructions = build_bend_instructions(
        tube
    )

    assert instructions.items == ()
    assert instructions.bend_count == 0
    assert instructions.cut_length_mm == pytest.approx(
        1000.0
    )


def test_invalid_mark_reference_is_rejected():
    with pytest.raises(
        ValueError,
    ):
        build_bend_instructions(
            _tube(),
            mark_reference="unsupported",
        )
