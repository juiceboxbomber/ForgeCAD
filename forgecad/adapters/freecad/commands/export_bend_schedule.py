"""FreeCAD command for exporting a selected bent-tube bend schedule."""

from pathlib import Path

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.commands.bend_schedule import (
    bend_report_for_object,
    selected_bent_tube_object,
)
from forgecad.services.bend_report_csv import (
    bend_report_to_csv,
)


COMMAND_NAME = "ForgeCAD_ExportBendSchedule"


def default_export_name(
    obj,
) -> str:
    """Return a filesystem-friendly default CSV file name."""

    name = str(
        getattr(
            obj,
            "TubeName",
            "",
        )
    ).strip()

    if not name:
        name = str(
            getattr(
                obj,
                "Label",
                "Bent Tube",
            )
        ).strip()

    if not name:
        name = "Bent Tube"

    safe = "".join(
        character
        if (
            character.isalnum()
            or character in (
                "-",
                "_",
                " ",
            )
        )
        else "_"
        for character in name
    ).strip()

    return (
        safe.replace(
            " ",
            "_",
        )
        + "_bend_schedule.csv"
    )


def write_bend_report_csv(
    path,
    report,
    tube_name,
):
    """Write bend report CSV to disk."""

    destination = Path(
        path
    )

    text = bend_report_to_csv(
        report,
        tube_name=tube_name,
    )

    destination.write_text(
        text,
        encoding="utf-8",
        newline="",
    )

    return destination


class ExportBendScheduleCommand:
    """Export one selected bent tube's bend schedule to CSV."""

    def GetResources(
        self,
    ):
        return {
            "MenuText": "Export Bend Schedule",
            "ToolTip": (
                "Export the selected bent tube's "
                "bend schedule to CSV"
            ),
        }

    def Activated(
        self,
    ):
        document = FreeCAD.ActiveDocument

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Document",
                "Open or create a ForgeCAD project first.",
            )
            return

        try:
            obj = selected_bent_tube_object()

            report = bend_report_for_object(
                document,
                obj,
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Cannot Export Bend Schedule",
                str(
                    error
                ),
            )
            return

        tube_name = str(
            getattr(
                obj,
                "TubeName",
                "",
            )
        ).strip()

        if not tube_name:
            tube_name = str(
                getattr(
                    obj,
                    "Label",
                    "Bent Tube",
                )
            ).strip()

        default_name = default_export_name(
            obj
        )

        path, _selected_filter = (
            QtGui.QFileDialog.getSaveFileName(
                FreeCADGui.getMainWindow(),
                "Export Bend Schedule",
                default_name,
                "CSV Files (*.csv)",
            )
        )

        if not path:
            return

        try:
            write_bend_report_csv(
                path,
                report,
                tube_name,
            )

        except OSError as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Cannot Export Bend Schedule",
                str(
                    error
                ),
            )
            return

        QtGui.QMessageBox.information(
            FreeCADGui.getMainWindow(),
            "Bend Schedule Exported",
            (
                "Bend schedule exported to:\n"
                f"{path}"
            ),
        )

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command():
    """Register the Export Bend Schedule command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        ExportBendScheduleCommand(),
    )
