"""Tests for tooling-aware bent-tube creation."""

import pytest

from forgecad.fabrication import (
    Bend,
    BenderTooling,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.services.bent_tube_tooling import (
    ToolingAwareBentTube,
    attach_tooling,
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


def _tube(
    radius=100.0,
):
    return BentTube(
        straight_runs=(
            StraightRun(500.0),
            StraightRun(750.0),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=radius,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


def test_tooling_is_optional():
    result = attach_tooling(
        _tube(),
        None,
    )

    assert result.has_tooling is False
    assert result.machine_instructions() is None


def test_matching_tooling_is_accepted():
    tooling = BenderTooling(
        name="100 mm CLR Die",
        centerline_radius_mm=100.0,
    )

    result = attach_tooling(
        _tube(),
        tooling,
    )

    assert result.has_tooling is True
    assert result.tooling is tooling


def test_matching_tooling_generates_machine_instructions():
    tooling = BenderTooling(
        name="100 mm CLR Die",
        centerline_radius_mm=100.0,
        mark_offset_mm=5.0,
        angle_compensation_degrees=2.0,
    )

    result = attach_tooling(
        _tube(),
        tooling,
    )

    instructions = result.machine_instructions()

    assert instructions is not None
    assert instructions.tooling_name == "100 mm CLR Die"
    assert instructions.bend_count == 1
    assert instructions.items[0].mark_position_mm == pytest.approx(
        505.0
    )
    assert instructions.items[0].bend_angle_degrees == pytest.approx(
        92.0
    )


def test_wrong_tooling_radius_is_rejected_immediately():
    tooling = BenderTooling(
        name="125 mm CLR Die",
        centerline_radius_mm=125.0,
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        attach_tooling(
            _tube(),
            tooling,
        )


def test_multi_bend_tube_requires_all_bends_to_match_tooling():
    tube = BentTube(
        straight_runs=(
            StraightRun(400.0),
            StraightRun(500.0),
            StraightRun(600.0),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
            Bend(
                angle_degrees=45.0,
                centerline_radius=125.0,
                rotation_degrees=90.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )

    tooling = BenderTooling(
        name="100 mm CLR Die",
        centerline_radius_mm=100.0,
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        ToolingAwareBentTube(
            tube=tube,
            tooling=tooling,
        )
