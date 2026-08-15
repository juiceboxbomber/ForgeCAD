"""Tests for ForgeCAD shop-ready bend reports."""

import pytest

from forgecad.fabrication import (
    Bend,
    BenderTooling,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.services.bend_report import (
    build_bend_report,
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


def _single_bend_tube():
    return BentTube(
        straight_runs=(
            StraightRun(
                500.0
            ),
            StraightRun(
                750.0
            ),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
                rotation_degrees=0.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


def _multi_bend_tube():
    return BentTube(
        straight_runs=(
            StraightRun(
                400.0
            ),
            StraightRun(
                500.0
            ),
            StraightRun(
                600.0
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


def test_report_without_tooling_uses_ideal_bend_values():
    tube = _single_bend_tube()

    report = build_bend_report(
        tube
    )

    assert report.tooling_name is None
    assert report.bend_count == 1

    row = report.rows[0]

    assert row.bend_number == 1

    assert (
        row.mark_position_mm
        == pytest.approx(
            500.0
        )
    )

    assert (
        row.bend_angle_degrees
        == pytest.approx(
            90.0
        )
    )

    assert (
        row.centerline_radius_mm
        == pytest.approx(
            100.0
        )
    )

    assert (
        row.rotation_degrees
        == pytest.approx(
            0.0
        )
    )


def test_report_with_tooling_applies_mark_offset():
    tube = _single_bend_tube()

    tooling = BenderTooling(
        name="100 mm CLR Die",
        centerline_radius_mm=100.0,
        mark_offset_mm=5.0,
    )

    report = build_bend_report(
        tube,
        tooling,
    )

    assert (
        report.rows[
            0
        ].mark_position_mm
        == pytest.approx(
            505.0
        )
    )


def test_report_with_tooling_applies_angle_compensation():
    tube = _single_bend_tube()

    tooling = BenderTooling(
        name="100 mm CLR Die",
        centerline_radius_mm=100.0,
        angle_compensation_degrees=2.5,
    )

    report = build_bend_report(
        tube,
        tooling,
    )

    assert (
        report.rows[
            0
        ].bend_angle_degrees
        == pytest.approx(
            92.5
        )
    )


def test_report_preserves_bend_rotation():
    tube = _multi_bend_tube()

    tooling = BenderTooling(
        name="100 mm CLR Die",
        centerline_radius_mm=100.0,
    )

    report = build_bend_report(
        tube,
        tooling,
    )

    assert (
        report.rows[
            1
        ].rotation_degrees
        == pytest.approx(
            90.0
        )
    )


def test_report_cut_length_matches_developed_length():
    tube = _single_bend_tube()

    report = build_bend_report(
        tube
    )

    assert (
        report.cut_length_mm
        == pytest.approx(
            tube.developed_length
        )
    )


def test_multi_bend_report_preserves_order():
    tube = _multi_bend_tube()

    tooling = BenderTooling(
        name="100 mm CLR Die",
        centerline_radius_mm=100.0,
    )

    report = build_bend_report(
        tube,
        tooling,
    )

    assert report.bend_count == 2

    assert [
        row.bend_number
        for row in report.rows
    ] == [
        1,
        2,
    ]

    assert [
        row.bend_angle_degrees
        for row in report.rows
    ] == [
        pytest.approx(
            90.0
        ),
        pytest.approx(
            45.0
        ),
    ]

    assert report.tooling_name == (
        "100 mm CLR Die"
    )
    