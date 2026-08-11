"""Show a summary of ForgeCAD joint review progress."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.joint_status_adapter import (
    joint_review_for_document,
)


COMMAND_NAME = (
    "ForgeCAD_JointReviewSummary"
)


def summary_text(
    summary,
):
    """Return display text for a joint-review summary."""

    return (
        f"Total Joints: {summary.total_joints}\n"
        f"Reviewed: {summary.reviewed_joints}\n"
        f"Unreviewed: {summary.unreviewed_joints}\n"
        f"\n"
        f"Automatic: {summary.automatic_treatments}\n"
        f"Manual Treatments: {summary.manual_treatments}\n"
        f"Invalid: {summary.invalid_treatments}\n"
        f"Needs Attention: {summary.attention_joints}\n"
        f"\n"
        f"Review Complete: {summary.review_percent:.1f}%"
    )


def summary_title(
    summary,
):
    """Return an appropriate dialog title."""

    if (
        summary.total_joints == 0
    ):
        return (
            "Joint Review Summary"
        )

    if (
        summary.attention_joints == 0
    ):
        return (
            "Joint Review Complete"
        )

    return (
        "Joint Review Summary"
    )


class JointReviewSummaryCommand:
    """Display joint-review progress for the active document."""

    def GetResources(
        self,
    ):
        return {
            "MenuText":
                "Joint Review Summary",
            "ToolTip": (
                "Show review progress and treatment "
                "counts for ForgeCAD joints"
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

        review = (
            joint_review_for_document(
                document
            )
        )

        summary = (
            review.summary
        )

        if (
            summary.total_joints == 0
        ):
            QtGui.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "Joint Review Summary",
                (
                    "No frame joints are available.\n\n"
                    "Generate a ForgeCAD frame first."
                ),
            )
            return

        QtGui.QMessageBox.information(
            FreeCADGui.getMainWindow(),
            summary_title(
                summary
            ),
            summary_text(
                summary
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
        JointReviewSummaryCommand(),
    )
    