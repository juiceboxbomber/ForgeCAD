"""Tests for ForgeCAD bend-report CSV export."""

from forgecad.services.bend_report import (
    BendReport,
    BendReportRow,
)
from forgecad.services.bend_report_csv import (
    bend_report_to_csv,
)


def _report():
    return BendReport(
        tooling_name="100 mm CLR Die",
        cut_length_mm=1500.0,
        rows=(
            BendReportRow(
                bend_number=1,
                mark_position_mm=500.0,
                bend_angle_degrees=92.0,
                centerline_radius_mm=100.0,
                rotation_degrees=0.0,
            ),
            BendReportRow(
                bend_number=2,
                mark_position_mm=1157.079632,
                bend_angle_degrees=47.0,
                centerline_radius_mm=100.0,
                rotation_degrees=90.0,
            ),
        ),
    )


def test_csv_contains_report_metadata():
    text = bend_report_to_csv(
        _report(),
        tube_name="Main Hoop",
    )

    assert "Tube Name,Main Hoop" in text
    assert "Tooling,100 mm CLR Die" in text
    assert "Cut Length (mm),1500.000" in text


def test_csv_contains_bend_headers():
    text = bend_report_to_csv(
        _report()
    )

    assert (
        "Bend,Mark Position (mm),Bend Angle (deg),"
        "CLR (mm),Rotation (deg)"
    ) in text


def test_csv_preserves_bend_order_and_values():
    text = bend_report_to_csv(
        _report()
    )

    assert "1,500.000,92.000,100.000,0.000" in text
    assert "2,1157.080,47.000,100.000,90.000" in text


def test_csv_blank_tube_name_uses_default():
    text = bend_report_to_csv(
        _report(),
        tube_name="   ",
    )

    assert "Tube Name,Bent Tube" in text


def test_csv_rejects_wrong_report_type():
    try:
        bend_report_to_csv(
            object()
        )
        assert False
    except TypeError as error:
        assert "BendReport" in str(
            error
        )
