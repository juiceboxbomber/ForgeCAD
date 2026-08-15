"""PDF fabrication-sheet renderer for ForgeCAD bent tubes."""

from pathlib import Path



from forgecad.services.bend_fabrication_sheet import (
    BendFabricationSheet,
)


PAGE_WIDTH = 612.0
PAGE_HEIGHT = 792.0

LEFT_MARGIN = 36.0
RIGHT_MARGIN = 36.0
TOP_MARGIN = 36.0
BOTTOM_MARGIN = 36.0

TITLE_SIZE = 16
SECTION_SIZE = 10
BODY_SIZE = 9

ROW_HEIGHT = 20.0

COLUMN_WIDTHS = (
    44.0,
    118.0,
    118.0,
    90.0,
    104.0,
)

TABLE_HEADERS = (
    "Bend",
    "Mark Position (mm)",
    "Bend Angle (deg)",
    "CLR (mm)",
    "Rotation (deg)",
)


def _draw_text(
    pdf,
    x,
    y,
    text,
    size=BODY_SIZE,
    bold=False,
):
    """Draw one line of PDF text."""

    font_name = (
        "Helvetica-Bold"
        if bold
        else "Helvetica"
    )

    pdf.setFont(
        font_name,
        size,
    )

    pdf.drawString(
        x,
        y,
        str(
            text
        ),
    )


def _draw_table_row(
    pdf,
    y,
    values,
    header=False,
):
    """Draw one bend-table row and return the next y position."""

    x = LEFT_MARGIN

    for width, value in zip(
        COLUMN_WIDTHS,
        values,
    ):
        pdf.rect(
            x,
            y - ROW_HEIGHT,
            width,
            ROW_HEIGHT,
            stroke=1,
            fill=0,
        )

        _draw_text(
            pdf,
            x + 5.0,
            y - 13.5,
            value,
            size=8,
            bold=header,
        )

        x += width

    return y - ROW_HEIGHT


def render_bend_fabrication_sheet_pdf(
    sheet: BendFabricationSheet,
    output_path,
):
    """Render one ForgeCAD bend fabrication sheet as a PDF."""

    if not isinstance(
        sheet,
        BendFabricationSheet,
    ):
        raise TypeError(
            "sheet must be a BendFabricationSheet instance."
        )

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as error:
        raise RuntimeError(
            "PDF export requires the ReportLab Python package."
        ) from error

    destination = Path(
        output_path
    )

    pdf = canvas.Canvas(
        str(
            destination
        ),
        pagesize=letter,
    )
    

    pdf.setTitle(
        f"ForgeCAD Bend Fabrication Sheet - {sheet.tube_name}"
    )

    y = PAGE_HEIGHT - TOP_MARGIN

    _draw_text(
        pdf,
        LEFT_MARGIN,
        y,
        "ForgeCAD Bend Fabrication Sheet",
        size=TITLE_SIZE,
        bold=True,
    )

    y -= 28.0

    metadata = (
        (
            "Tube Name",
            sheet.tube_name,
        ),
        (
            "Material",
            sheet.material_name,
        ),
        (
            "Outside Diameter",
            f"{sheet.outside_diameter_mm:.3f} mm",
        ),
        (
            "Wall Thickness",
            f"{sheet.wall_thickness_mm:.3f} mm",
        ),
        (
            "Inside Diameter",
            f"{sheet.inside_diameter_mm:.3f} mm",
        ),
        (
            "Tooling",
            sheet.tooling_name or "None",
        ),
        (
            "Cut Length",
            f"{sheet.cut_length_mm:.3f} mm",
        ),
        (
            "Bend Count",
            str(
                sheet.bend_count
            ),
        ),
    )

    for label, value in metadata:
        _draw_text(
            pdf,
            LEFT_MARGIN,
            y,
            f"{label}:",
            bold=True,
        )
        _draw_text(
            pdf,
            LEFT_MARGIN + 125.0,
            y,
            value,
        )
        y -= 15.0

    y -= 12.0

    _draw_text(
        pdf,
        LEFT_MARGIN,
        y,
        "Bend Schedule",
        size=SECTION_SIZE,
        bold=True,
    )

    y -= 8.0

    y = _draw_table_row(
        pdf,
        y,
        TABLE_HEADERS,
        header=True,
    )

    for row in sheet.rows:
        if (
            y - ROW_HEIGHT
            < BOTTOM_MARGIN
        ):
            pdf.showPage()
            y = (
                PAGE_HEIGHT
                - TOP_MARGIN
            )

            _draw_text(
                pdf,
                LEFT_MARGIN,
                y,
                (
                    "ForgeCAD Bend Fabrication Sheet "
                    f"- {sheet.tube_name}"
                ),
                size=SECTION_SIZE,
                bold=True,
            )

            y -= 18.0

            y = _draw_table_row(
                pdf,
                y,
                TABLE_HEADERS,
                header=True,
            )

        y = _draw_table_row(
            pdf,
            y,
            (
                str(
                    row.bend_number
                ),
                f"{row.mark_position_mm:.3f}",
                f"{row.bend_angle_degrees:.3f}",
                f"{row.centerline_radius_mm:.3f}",
                f"{row.rotation_degrees:.3f}",
            ),
        )

    y -= 18.0

    if (
        y
        < BOTTOM_MARGIN + 50.0
    ):
        pdf.showPage()
        y = (
            PAGE_HEIGHT
            - TOP_MARGIN
        )

    _draw_text(
        pdf,
        LEFT_MARGIN,
        y,
        "Fabrication Notes",
        size=SECTION_SIZE,
        bold=True,
    )

    y -= 16.0

    notes = (
        "Mark positions are measured from the tube start along the "
        "developed centerline.",
        "Bend angles and mark positions include tooling compensation "
        "when tooling is assigned.",
        "Rotation is the clocking angle for the bend relative to the "
        "current tube direction.",
        "Verify machine setup and calibration before fabrication.",
    )

    for note in notes:
        _draw_text(
            pdf,
            LEFT_MARGIN + 8.0,
            y,
            f"- {note}",
            size=8,
        )
        y -= 13.0

    pdf.save()

    return destination
