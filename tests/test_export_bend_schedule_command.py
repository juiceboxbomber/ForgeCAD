"""Tests for ForgeCAD bend-schedule CSV export command helpers."""

import sys
import types

from forgecad.services.bend_report import (
    BendReport,
    BendReportRow,
)


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)
fake_part = types.ModuleType(
    "Part"
)

fake_freecad_gui.Selection = types.SimpleNamespace(
    getSelection=lambda: []
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "FreeCADGui"
] = fake_freecad_gui
sys.modules[
    "Part"
] = fake_part


fake_pyside = types.ModuleType(
    "PySide"
)

fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=object,
)

sys.modules[
    "PySide"
] = fake_pyside


from forgecad.adapters.freecad.commands.export_bend_schedule import (
    default_export_name,
    write_bend_report_csv,
)


class FakeObject:
    TubeName = "Main Hoop"
    Label = "Bent Tube"


def _report():
    return BendReport(
        tooling_name=None,
        cut_length_mm=1000.0,
        rows=(
            BendReportRow(
                bend_number=1,
                mark_position_mm=400.0,
                bend_angle_degrees=90.0,
                centerline_radius_mm=100.0,
                rotation_degrees=0.0,
            ),
        ),
    )


def test_default_export_name_uses_tube_name():
    assert default_export_name(
        FakeObject()
    ) == (
        "Main_Hoop_bend_schedule.csv"
    )


def test_default_export_name_sanitizes_characters():
    obj = FakeObject()
    obj.TubeName = "Main/Hoop #1"

    assert default_export_name(
        obj
    ) == (
        "Main_Hoop__1_bend_schedule.csv"
    )


def test_write_bend_report_csv_writes_expected_file(
    tmp_path,
):
    path = tmp_path / "schedule.csv"

    result = write_bend_report_csv(
        path,
        _report(),
        "Main Hoop",
    )

    assert result == path

    text = path.read_text(
        encoding="utf-8"
    )

    assert "Tube Name,Main Hoop" in text
    assert "1,400.000,90.000,100.000,0.000" in text
