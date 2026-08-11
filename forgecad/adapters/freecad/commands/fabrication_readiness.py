"""Show ForgeCAD fabrication-readiness status."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.frame_validation_adapter import (
    frame_validation_for_document,
)


COMMAND_NAME = (
    "ForgeCAD_FabricationReadiness"
)


def readiness_title(
    result,
):
    """Return an appropriate dialog title."""

    if result.is_ready:
        return (
            "Frame Ready"
        )

    return (
        "Frame Not Ready"
    )


def readiness_text(
    result,
):
    """Return display text for frame fabrication readiness."""

    if (
        result.total_joints == 0
    ):
        return (
            "No frame joints are available.\n\n"
            "Generate a ForgeCAD frame first."
        )

    if result.is_ready:
        return (
            "Frame Ready for Fabrication\n\n"
            f"Total Joints: {result.total_joints}\n"
            f"Ready Joints: {result.ready_joints}\n"
            "All joints have valid reviewed treatments."
        )

    return (
        "Frame Not Ready for Fabrication\n\n"
        f"Total Joints: {result.total_joints}\n"
        f"Ready Joints: {result.ready_joints}\n"
        f"Not Ready: {result.not_ready_joints}\n"
        f"Invalid: {result.invalid_joints}"
    )


class FabricationReadinessCommand:
    """Display fabrication-readiness status for the active frame."""

    def GetResources(
        self,
    ):
        return {
            "MenuText":
                "Fabrication Readiness",
            "ToolTip": (
                "Check whether all ForgeCAD joints "
                "are ready for fabrication"
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
                "No Active Document",
                (
                    "Open or create a ForgeCAD "
                    "project first."
                ),
            )
            return

        result = (
            frame_validation_for_document(
                document
            )
        )

        QtGui.QMessageBox.information(
            FreeCADGui.getMainWindow(),
            readiness_title(
                result
            ),
            readiness_text(
                result
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
    """Register the command with FreeCAD."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        FabricationReadinessCommand(),
    )
    