"""Tests for diagram rendering in ForgeCAD fabrication-sheet PDFs."""

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.services.bend_fabrication_pdf import (
    render_bend_fabrication_sheet_pdf,
)
from forgecad.services.bend_fabrication_sheet import (
    build_bend_fabrication_sheet,
)


def _sheet():
    tube = BentTube(
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
    return build_bend_fabrication_sheet(tube, "Main Hoop")


def test_pdf_with_bend_diagram_creates_nonempty_file(tmp_path):
    output = tmp_path / "diagram_sheet.pdf"
    render_bend_fabrication_sheet_pdf(_sheet(), output)

    assert output.exists()
    assert output.stat().st_size > 1000


def test_pdf_with_bend_diagram_has_pdf_signature(tmp_path):
    output = tmp_path / "diagram_sheet.pdf"
    render_bend_fabrication_sheet_pdf(_sheet(), output)

    assert output.read_bytes()[:4] == b"%PDF"
