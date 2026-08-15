"""FreeCAD command for editing project bender tooling."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.bender_library_store import (
    load_bender_library,
    save_bender_library,
)
from forgecad.adapters.freecad.dialogs.bender_tooling_settings import (
    BenderToolingSettingsDialog,
)


COMMAND_NAME = "ForgeCAD_BenderToolingSettings"


class BenderToolingSettingsCommand:
    """Edit persistent bender tooling for the active ForgeCAD project."""

    def GetResources(self):
        return {
            "MenuText": "Bender Tooling",
            "ToolTip": (
                "Configure tubing bender dies, CLR, "
                "mark offsets, and angle compensation"
            ),
        }

    def Activated(self):
        document = FreeCAD.ActiveDocument

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Project",
                "Create or open a ForgeCAD project first.",
            )
            return

        library = load_bender_library(document)

        dialog = BenderToolingSettingsDialog(
            library,
            FreeCADGui.getMainWindow(),
        )

        if dialog.exec_() != QtGui.QDialog.Accepted:
            return

        try:
            save_bender_library(
                document,
                dialog.library,
            )
        except (KeyError, TypeError, ValueError) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Bender Tooling",
                str(error),
            )

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


def register_command() -> None:
    """Register the Bender Tooling Settings command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        BenderToolingSettingsCommand(),
    )
