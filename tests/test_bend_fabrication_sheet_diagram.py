"""Tests for bend-path data on ForgeCAD fabrication sheets."""

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.services.bend_fabrication_sheet import (
    build_bend_fabrication_sheet,
)


def _tube():
    return BentTube(
        straight_runs=(
            StraightRun(500.0),
            StraightRun(500.0),
            StraightRun(500.0),
        ),
        bends=(
            Bend(90.0, 100.0, 0.0),
            Bend(90.0, 100.0, 90.0),
        ),
        profile=TubeProfile(44.45, 3.048),
        material=Material("A513 Type 5 DOM", 7850.0, 350.0),
    )


def test_fabrication_sheet_contains_bend_path_diagram():
    sheet = build_bend_fabrication_sheet(_tube(), "Main Hoop")

    assert sheet.diagram is not None
    assert len(sheet.diagram.segments) == 5
    assert [segment.kind for segment in sheet.diagram.segments] == [
        "straight",
        "arc",
        "straight",
        "arc",
        "straight",
    ]


def test_fabrication_sheet_diagram_records_projection_axes():
    sheet = build_bend_fabrication_sheet(_tube(), "Main Hoop")

    assert len(sheet.diagram.axes) == 2
    assert all(axis in ("x", "y", "z") for axis in sheet.diagram.axes)
