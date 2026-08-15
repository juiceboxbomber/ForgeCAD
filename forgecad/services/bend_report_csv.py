"""CSV export for ForgeCAD bend reports."""

import csv
import io

from forgecad.services.bend_report import (
    BendReport,
)


CSV_HEADERS = (
    "Bend",
    "Mark Position (mm)",
    "Bend Angle (deg)",
    "CLR (mm)",
    "Rotation (deg)",
)


def bend_report_to_csv(
    report: BendReport,
    tube_name: str = "Bent Tube",
) -> str:
    """Return one bend report as shop-ready CSV text."""

    if not isinstance(
        report,
        BendReport,
    ):
        raise TypeError(
            "report must be a BendReport instance."
        )

    name = str(
        tube_name
    ).strip()

    if not name:
        name = "Bent Tube"

    stream = io.StringIO(
        newline=""
    )

    writer = csv.writer(
        stream
    )

    writer.writerow(
        (
            "Tube Name",
            name,
        )
    )

    writer.writerow(
        (
            "Tooling",
            report.tooling_name or "",
        )
    )

    writer.writerow(
        (
            "Cut Length (mm)",
            f"{report.cut_length_mm:.3f}",
        )
    )

    writer.writerow(
        ()
    )

    writer.writerow(
        CSV_HEADERS
    )

    for row in report.rows:
        writer.writerow(
            (
                row.bend_number,
                f"{row.mark_position_mm:.3f}",
                f"{row.bend_angle_degrees:.3f}",
                f"{row.centerline_radius_mm:.3f}",
                f"{row.rotation_degrees:.3f}",
            )
        )

    return stream.getvalue()
