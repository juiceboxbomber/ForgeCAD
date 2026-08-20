"""FreeCAD command for displaying a bent-tube bend schedule."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.bender_library_store import (
    load_bender_library,
)
from forgecad.adapters.freecad.dialogs.bend_schedule import (
    BendScheduleDialog,
)
from forgecad.services.bend_report import (
    build_bend_report,
)


COMMAND_NAME = "ForgeCAD_BendSchedule"


def selected_bent_tube_object():
    """Return the single selected ForgeCAD bent-tube object."""

    selection = FreeCADGui.Selection.getSelection()

    if len(
        selection
    ) != 1:
        raise ValueError(
            "Select exactly one ForgeCAD bent tube."
        )

    obj = selection[
        0
    ]

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

    return obj


def tooling_for_object(
    document,
    obj,
):
    """Return persisted tooling referenced by a bent-tube object."""

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


def bend_report_for_object(
    document,
    obj,
):
    """Build a bend report from one parametric bent-tube object."""

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

    return build_bend_report(
        tube,
        tooling,
    )


class BendScheduleCommand:
    """Display the bend schedule for one selected bent tube."""

    def GetResources(
        self,
    ):
        return {
            "MenuText": "Bend Schedule",
            "ToolTip": (
                "Show bend marks, angles, CLR, rotation, "
                "tooling, and cut length for a selected bent tube"
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
                "Cannot Build Bend Schedule",
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
            )

        dialog = BendScheduleDialog(
            report,
            tube_name=tube_name,
            parent=FreeCADGui.getMainWindow(),
        )

        dialog.exec_()

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command():
    """Register the Bend Schedule command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        BendScheduleCommand(),
    )
