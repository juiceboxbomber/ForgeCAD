"""Tests for ForgeCAD bend fabrication-sheet data."""

import pytest

from forgecad.fabrication import (
    Bend,
    BenderTooling,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.services.bend_fabrication_sheet import (
    build_bend_fabrication_sheet,
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
            StraightRun(
                500.0
            ),
            StraightRun(
                600.0
            ),
            StraightRun(
                700.0
            ),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
                rotation_degrees=0.0,
            ),
            Bend(
                angle_degrees=45.0,
                centerline_radius=100.0,
                rotation_degrees=90.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


def test_sheet_contains_tube_identity_and_material():
    sheet = build_bend_fabrication_sheet(
        _tube(),
        "Main Hoop",
    )

    assert sheet.tube_name == "Main Hoop"
    assert sheet.material_name == "A513 Type 5 DOM"


def test_sheet_contains_tube_dimensions():
    sheet = build_bend_fabrication_sheet(
        _tube(),
        "Main Hoop",
    )

    assert (
        sheet.outside_diameter_mm
        == pytest.approx(
            44.45
        )
    )
    assert (
        sheet.wall_thickness_mm
        == pytest.approx(
            3.048
        )
    )
    assert (
        sheet.inside_diameter_mm
        == pytest.approx(
            44.45 - 2.0 * 3.048
        )
    )


def test_sheet_reuses_bend_report_rows():
    sheet = build_bend_fabrication_sheet(
        _tube(),
        "Main Hoop",
    )

    assert sheet.bend_count == 2

    assert [
        row.bend_number
        for row in sheet.rows
    ] == [
        1,
        2,
    ]

    assert (
        sheet.rows[
            1
        ].rotation_degrees
        == pytest.approx(
            90.0
        )
    )


def test_sheet_includes_tooling_adjustments():
    tooling = BenderTooling(
        name="100 mm CLR Die",
        centerline_radius_mm=100.0,
        mark_offset_mm=5.0,
        angle_compensation_degrees=2.0,
    )

    sheet = build_bend_fabrication_sheet(
        _tube(),
        "Main Hoop",
        tooling,
    )

    assert sheet.tooling_name == "100 mm CLR Die"

    assert (
        sheet.rows[
            0
        ].mark_position_mm
        == pytest.approx(
            505.0
        )
    )

    assert (
        sheet.rows[
            0
        ].bend_angle_degrees
        == pytest.approx(
            92.0
        )
    )


def test_sheet_cut_length_matches_developed_tube_length():
    tube = _tube()

    sheet = build_bend_fabrication_sheet(
        tube,
        "Main Hoop",
    )

    assert (
        sheet.cut_length_mm
        == pytest.approx(
            tube.developed_length
        )
    )


def test_sheet_rejects_blank_tube_name():
    with pytest.raises(
        ValueError,
        match="Tube name",
    ):
        build_bend_fabrication_sheet(
            _tube(),
            "   ",
        )
