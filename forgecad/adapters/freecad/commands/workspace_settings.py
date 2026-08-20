"""FreeCAD command for editing ForgeCAD workspace settings."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.dialogs.workspace_settings import (
    WorkspaceSettingsDialog,
)
from forgecad.adapters.freecad.workspace import (
    WORKSPACE_OBJECT_NAME,
    configure_workspace_view,
    update_workspace_settings,
    workspace_settings_from_object,
)


COMMAND_NAME = "ForgeCAD_WorkspaceSettings"


def settings_from_dialog(
    dialog,
):
    """Return settings exposed by a Workspace Settings dialog."""

    return dialog.settings


class WorkspaceSettingsCommand:
    """Edit the active ForgeCAD project's layout workspace."""

    def GetResources(
        self,
    ):
        return {
            "MenuText": "Workspace Settings",
            "ToolTip": (
                "Edit ForgeCAD workspace size, "
                "grid spacing, visibility, and snapping"
            ),
        }

    def Activated(
        self,
    ):
        document = (
            FreeCAD.ActiveDocument
        )

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Project",
                (
                    "Create or open a ForgeCAD "
                    "project first."
                ),
            )
            return

        workspace_object = (
            document.getObject(
                WORKSPACE_OBJECT_NAME
            )
        )

        if workspace_object is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Workspace Not Found",
                (
                    "This document does not contain "
                    "a ForgeCAD workspace."
                ),
            )
            return

        current_settings = (
            workspace_settings_from_object(
                workspace_object
            )
        )

        dialog = WorkspaceSettingsDialog(
            current_settings,
            FreeCADGui.getMainWindow(),
        )

        if (
            dialog.exec_()
            != QtGui.QDialog.Accepted
        ):
            return

        try:
            new_settings = (
                settings_from_dialog(
                    dialog
                )
            )

            update_workspace_settings(
                document,
                new_settings,
            )

        except (
            TypeError,
            ValueError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Workspace Settings",
                str(
                    error
                ),
            )
            return

        configure_workspace_view()

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Workspace Settings command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        WorkspaceSettingsCommand(),
    )
