"""FreeCAD command for exporting a bent-tube fabrication sheet."""

from pathlib import Path

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.bender_library_store import (
    load_bender_library,
)
from forgecad.adapters.freecad.commands.bend_schedule import (
    selected_bent_tube_object,
)
from forgecad.services.bend_fabrication_pdf import (
    render_bend_fabrication_sheet_pdf,
)
from forgecad.services.bend_fabrication_sheet import (
    build_bend_fabrication_sheet,
)


COMMAND_NAME = "ForgeCAD_ExportBendFabricationSheet"


def tube_name_for_object(
    obj,
) -> str:
    """Return the display name for one bent-tube object."""

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

    return name or "Bent Tube"


def default_export_name(
    obj,
) -> str:
    """Return a filesystem-friendly default PDF filename."""

    name = tube_name_for_object(
        obj
    )

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
        + "_fabrication_sheet.pdf"
    )


def tooling_for_object(
    document,
    obj,
):
    """Return tooling assigned to a bent-tube object, if any."""

    tooling_name = str(
        getattr(
            obj,
            "BenderTooling",
            "",
        )
    ).strip()

    if not tooling_name:
        return None

    library = load_bender_library(
        document
    )

    return library.get(
        tooling_name
    )


def fabrication_sheet_for_object(
    document,
    obj,
):
    """Build fabrication-sheet data from a parametric bent tube."""

    proxy = getattr(
        obj,
        "Proxy",
        None,
    )

    if (
        proxy is None
        or not hasattr(
            proxy,
            "_tube_from_properties",
        )
    ):
        raise ValueError(
            "The selected object is not a ForgeCAD bent tube."
        )

    tube = proxy._tube_from_properties(
        obj
    )

    tooling = tooling_for_object(
        document,
        obj,
    )

    return build_bend_fabrication_sheet(
        tube,
        tube_name_for_object(
            obj
        ),
        tooling,
    )


def write_fabrication_sheet_pdf(
    path,
    sheet,
):
    """Render a fabrication sheet to the requested PDF path."""

    destination = Path(
        path
    )

    return render_bend_fabrication_sheet_pdf(
        sheet,
        destination,
    )


class ExportBendFabricationSheetCommand:
    """Export a printable fabrication sheet for one selected bent tube."""

    def GetResources(
        self,
    ):
        return {
            "MenuText": "Export Fabrication Sheet",
            "ToolTip": (
                "Export a printable PDF fabrication sheet "
                "for the selected bent tube"
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

            sheet = fabrication_sheet_for_object(
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
                "Cannot Export Fabrication Sheet",
                str(
                    error
                ),
            )
            return

        default_name = default_export_name(
            obj
        )

        path, _selected_filter = (
            QtGui.QFileDialog.getSaveFileName(
                FreeCADGui.getMainWindow(),
                "Export Fabrication Sheet",
                default_name,
                "PDF Files (*.pdf)",
            )
        )

        if not path:
            return

        if not str(
            path
        ).lower().endswith(
            ".pdf"
        ):
            path = (
                str(
                    path
                )
                + ".pdf"
            )

        try:
            write_fabrication_sheet_pdf(
                path,
                sheet,
            )

        except (
            OSError,
            RuntimeError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Cannot Export Fabrication Sheet",
                str(
                    error
                ),
            )
            return

        QtGui.QMessageBox.information(
            FreeCADGui.getMainWindow(),
            "Fabrication Sheet Exported",
            (
                "Fabrication sheet exported to:\n"
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
    """Register the Export Fabrication Sheet command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        ExportBendFabricationSheetCommand(),
    )
