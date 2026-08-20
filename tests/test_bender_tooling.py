"""Tests for ForgeCAD tubing-bender tooling."""

import pytest

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.fabrication import (
    BendMarkReference,
)
from forgecad.services.bender_setup import (
    build_machine_bend_instructions,
)
from forgecad.fabrication import (
    BenderTooling,
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


def test_tooling_stores_reference_and_calibration():
    tooling = BenderTooling(
        name="1.75 DOM Die",
        centerline_radius_mm=100.0,
        mark_reference=(
            BendMarkReference.CENTER_OF_BEND
        ),
        mark_offset_mm=4.5,
        angle_compensation_degrees=2.0,
    )

    assert tooling.name == "1.75 DOM Die"
    assert tooling.centerline_radius_mm == 100.0
    assert (
        tooling.mark_reference
        == BendMarkReference.CENTER_OF_BEND
    )
    assert tooling.mark_offset_mm == 4.5
    assert tooling.angle_compensation_degrees == 2.0


def test_machine_instruction_applies_mark_offset_and_springback():
    tooling = BenderTooling(
        name="Test Die",
        centerline_radius_mm=100.0,
        mark_reference=(
            BendMarkReference.START_TANGENT
        ),
        mark_offset_mm=5.0,
        angle_compensation_degrees=3.0,
    )

    instructions = (
        build_machine_bend_instructions(
            _tube(),
            tooling,
        )
    )

    item = instructions.items[0]

    assert item.mark_position_mm == pytest.approx(
        505.0
    )
    assert item.bend_angle_degrees == pytest.approx(
        93.0
    )
    assert item.rotation_degrees == pytest.approx(
        0.0
    )


def test_center_reference_uses_center_mark_before_offset():
    tooling = BenderTooling(
        name="Center Mark Die",
        centerline_radius_mm=100.0,
        mark_reference=(
            BendMarkReference.CENTER_OF_BEND
        ),
        mark_offset_mm=10.0,
    )

    instructions = (
        build_machine_bend_instructions(
            _tube(),
            tooling,
        )
    )

    expected = (
        500.0
        + _tube().bends[0].arc_length / 2.0
        + 10.0
    )

    assert (
        instructions.items[0].mark_position_mm
        == pytest.approx(expected)
    )


def test_tooling_radius_must_match_tube_bend_radius():
    tooling = BenderTooling(
        name="Wrong Die",
        centerline_radius_mm=125.0,
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        build_machine_bend_instructions(
            _tube(),
            tooling,
        )


def test_tooling_name_cannot_be_empty():
    with pytest.raises(
        ValueError,
        match="name",
    ):
        BenderTooling(
            name="   ",
            centerline_radius_mm=100.0,
        )


def test_tooling_radius_must_be_positive():
    with pytest.raises(
        ValueError,
        match="centerline radius",
    ):
        BenderTooling(
            name="Bad Die",
            centerline_radius_mm=0.0,
        )
