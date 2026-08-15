"""Tests for ForgeCAD bend fabrication-sheet PDF rendering."""

from pathlib import Path

import pytest

from forgecad.services.bend_fabrication_sheet import (
    BendFabricationSheet,
)
from forgecad.services.bend_report import (
    BendReportRow,
)
from forgecad.services.bend_fabrication_pdf import (
    render_bend_fabrication_sheet_pdf,
)


def _sheet():
    return BendFabricationSheet(
        tube_name="Main Hoop",
        material_name="A513 Type 5 DOM",
        outside_diameter_mm=44.45,
        wall_thickness_mm=3.048,
        inside_diameter_mm=38.354,
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
                mark_position_mm=1157.080,
                bend_angle_degrees=47.0,
                centerline_radius_mm=100.0,
                rotation_degrees=90.0,
            ),
        ),
    )


def test_pdf_renderer_creates_nonempty_file(
    tmp_path,
):
    output = (
        tmp_path
        / "main_hoop.pdf"
    )

    result = (
        render_bend_fabrication_sheet_pdf(
            _sheet(),
            output,
        )
    )

    assert result == output
    assert output.exists()
    assert output.stat().st_size > 500


def test_pdf_renderer_writes_pdf_signature(
    tmp_path,
):
    output = (
        tmp_path
        / "main_hoop.pdf"
    )

    render_bend_fabrication_sheet_pdf(
        _sheet(),
        output,
    )

    assert (
        output.read_bytes()[
            :4
        ]
        == b"%PDF"
    )


def test_pdf_renderer_rejects_wrong_type(
    tmp_path,
):
    with pytest.raises(
        TypeError,
        match="BendFabricationSheet",
    ):
        render_bend_fabrication_sheet_pdf(
            object(),
            tmp_path / "bad.pdf",
        )
