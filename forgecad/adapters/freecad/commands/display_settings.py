"""FreeCAD command for editing ForgeCAD display settings."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.dialogs.display_settings import (
    DisplaySettingsDialog,
)
from forgecad.adapters.freecad.display import (
    WORKSPACE_OBJECT_NAME,
    apply_display_settings,
    display_settings_from_object,
)


COMMAND_NAME = "ForgeCAD_DisplaySettings"


def settings_from_dialog(
    dialog,
):
    """Return settings exposed by a Display Settings dialog."""

    return dialog.settings


class DisplaySettingsCommand:
    """Edit ForgeCAD workspace and layout display styling."""

    def GetResources(
        self,
    ):
        return {
            "MenuText": "Display Settings",
            "ToolTip": (
                "Change ForgeCAD grid, axis, "
                "and layout-line colors and widths"
            ),
        }

    def Activated(
        self,
    ):
        document = FreeCAD.ActiveDocument

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Project",
                "Create or open a ForgeCAD project first.",
            )
            return

        workspace_object = document.getObject(
            WORKSPACE_OBJECT_NAME
        )

        if workspace_object is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Workspace Not Found",
                "This document does not contain a ForgeCAD workspace.",
            )
            return

        current_settings = display_settings_from_object(
            workspace_object
        )

        dialog = DisplaySettingsDialog(
            current_settings,
            FreeCADGui.getMainWindow(),
        )

        if (
            dialog.exec_()
            != QtGui.QDialog.Accepted
        ):
            return

        try:
            apply_display_settings(
                document,
                settings_from_dialog(
                    dialog
                ),
                persist=True,
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Display Settings",
                str(error),
            )

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Display Settings command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        DisplaySettingsCommand(),
    )
