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

DIAGRAM_HEIGHT = 190.0
DIAGRAM_PADDING = 18.0
BEND_MARKER_RADIUS = 8.0
BEND_MARKER_OFFSET = 14.0

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


def _diagram_transform(
    diagram,
    x,
    y,
    width,
    height,
):
    """Return a point-mapping function that fits a diagram into a box."""

    usable_width = max(
        1.0,
        width - 2.0 * DIAGRAM_PADDING,
    )

    usable_height = max(
        1.0,
        height - 2.0 * DIAGRAM_PADDING,
    )

    source_width = max(
        diagram.width,
        1e-9,
    )

    source_height = max(
        diagram.height,
        1e-9,
    )

    scale = min(
        usable_width / source_width,
        usable_height / source_height,
    )

    drawn_width = (
        diagram.width
        * scale
    )

    drawn_height = (
        diagram.height
        * scale
    )

    x_offset = (
        x
        + DIAGRAM_PADDING
        + (
            usable_width
            - drawn_width
        )
        / 2.0
    )

    y_offset = (
        y
        + DIAGRAM_PADDING
        + (
            usable_height
            - drawn_height
        )
        / 2.0
    )

    def map_point(
        point,
    ):
        return (
            x_offset
            + point.x
            * scale,
            y_offset
            + point.y
            * scale,
        )

    return map_point


def _bend_marker_position(
    points,
    map_point,
):
    """
    Return an offset marker position near the middle of a bend.

    The marker is moved perpendicular to the local bend direction so
    the centerline does not pass directly through the bend number.
    """

    mid_index = (
        len(
            points
        )
        // 2
    )

    marker_point = points[
        mid_index
    ]

    previous_point = points[
        max(
            0,
            mid_index - 1,
        )
    ]

    next_point = points[
        min(
            len(
                points
            )
            - 1,
            mid_index + 1,
        )
    ]

    marker_x, marker_y = (
        map_point(
            marker_point
        )
    )

    previous_x, previous_y = (
        map_point(
            previous_point
        )
    )

    next_x, next_y = (
        map_point(
            next_point
        )
    )

    direction_x = (
        next_x
        - previous_x
    )

    direction_y = (
        next_y
        - previous_y
    )

    direction_length = (
        direction_x ** 2
        + direction_y ** 2
    ) ** 0.5

    if (
        direction_length
        <= 1e-9
    ):
        return (
            marker_x,
            marker_y
            + BEND_MARKER_OFFSET,
        )

    normal_x = (
        -direction_y
        / direction_length
    )

    normal_y = (
        direction_x
        / direction_length
    )

    return (
        marker_x
        + normal_x
        * BEND_MARKER_OFFSET,
        marker_y
        + normal_y
        * BEND_MARKER_OFFSET,
    )


def _draw_bend_path_diagram(
    pdf,
    diagram,
    x,
    y,
    width,
    height,
):
    """Draw a fitted bend-path centerline with bend-number markers."""

    pdf.rect(
        x,
        y,
        width,
        height,
        stroke=1,
        fill=0,
    )

    if diagram is None:
        _draw_text(
            pdf,
            x + 8.0,
            y + height / 2.0,
            "No bend-path diagram available.",
            size=8,
        )
        return

    map_point = _diagram_transform(
        diagram,
        x,
        y,
        width,
        height,
    )

    pdf.setLineWidth(
        1.5
    )

    bend_number = 0

    for segment in diagram.segments:
        points = segment.points

        for first, second in zip(
            points,
            points[
                1:
            ],
        ):
            x1, y1 = map_point(
                first
            )

            x2, y2 = map_point(
                second
            )

            pdf.line(
                x1,
                y1,
                x2,
                y2,
            )

        if (
            segment.kind
            == "arc"
        ):
            bend_number += 1

            marker_x, marker_y = (
                _bend_marker_position(
                    points,
                    map_point,
                )
            )

            pdf.circle(
                marker_x,
                marker_y,
                BEND_MARKER_RADIUS,
                stroke=1,
                fill=0,
            )

            pdf.setFont(
                "Helvetica-Bold",
                7,
            )

            pdf.drawCentredString(
                marker_x,
                marker_y - 2.5,
                str(
                    bend_number
                ),
            )

    axes_text = (
        f"Projection: "
        f"{diagram.axes[0].upper()}"
        f"{diagram.axes[1].upper()}"
    )

    _draw_text(
        pdf,
        x + 6.0,
        y + 6.0,
        axes_text,
        size=7,
    )


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

    y = (
        PAGE_HEIGHT
        - TOP_MARGIN
    )

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

    y -= 10.0

    _draw_text(
        pdf,
        LEFT_MARGIN,
        y,
        "Bend Path",
        size=SECTION_SIZE,
        bold=True,
    )

    y -= (
        DIAGRAM_HEIGHT
        + 8.0
    )

    _draw_bend_path_diagram(
        pdf,
        sheet.diagram,
        LEFT_MARGIN,
        y,
        PAGE_WIDTH
        - LEFT_MARGIN
        - RIGHT_MARGIN,
        DIAGRAM_HEIGHT,
    )

    y -= 18.0

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
        < BOTTOM_MARGIN + 70.0
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
        (
            "Mark positions are measured from the tube start along the "
            "developed centerline."
        ),
        (
            "Bend angles and mark positions include tooling compensation "
            "when tooling is assigned."
        ),
        (
            "Rotation is the clocking angle for the bend relative to the "
            "current tube direction."
        ),
        (
            "Verify machine setup and calibration before fabrication."
        ),
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
