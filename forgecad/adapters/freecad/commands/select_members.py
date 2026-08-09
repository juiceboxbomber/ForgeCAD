"""FreeCAD command for selecting ForgeCAD members by properties."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.services import (
    create_default_tube_library,
)


COMMAND_NAME = "ForgeCAD_SelectMembers"


def frame_members(document):
    """Return generated ForgeCAD members from the Frame group."""

    if document is None:
        return []

    frame_group = document.getObject(
        "ForgeCADFrame"
    )

    if frame_group is None:
        return []

    members = []

    for obj in frame_group.Group:
        if not hasattr(
            obj,
            "MemberID",
        ):
            continue

        if not hasattr(
            obj,
            "TubeProfile",
        ):
            continue

        members.append(
            obj
        )

    return members


def members_with_profile(
    members,
    profile_name,
):
    """Return members using the requested tube profile."""

    return [
        member
        for member in members
        if str(
            member.TubeProfile
        ) == profile_name
    ]


class SelectMembersDialog(QtGui.QDialog):
    """Select generated ForgeCAD members by tube profile."""

    def __init__(
        self,
        document,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.document = document

        self.members = frame_members(
            document
        )

        self.setWindowTitle(
            "Select ForgeCAD Members"
        )

        self.setMinimumWidth(
            420
        )

        # -----------------------------------------------------
        # Profile selector
        # -----------------------------------------------------

        self.profile_combo = (
            QtGui.QComboBox()
        )

        library = (
            create_default_tube_library()
        )

        for profile_name in library.names:
            self.profile_combo.addItem(
                profile_name
            )

        # -----------------------------------------------------
        # Match information
        # -----------------------------------------------------

        self.match_label = (
            QtGui.QLabel()
        )

        self.profile_combo.currentIndexChanged.connect(
            self.update_match_count
        )

        self.update_match_count()

        # -----------------------------------------------------
        # Form
        # -----------------------------------------------------

        form = (
            QtGui.QFormLayout()
        )

        form.addRow(
            "Tube Profile:",
            self.profile_combo,
        )

        form.addRow(
            "Found:",
            self.match_label,
        )

        # -----------------------------------------------------
        # Buttons
        # -----------------------------------------------------

        buttons = (
            QtGui.QDialogButtonBox(
                QtGui.QDialogButtonBox.Ok
                | QtGui.QDialogButtonBox.Cancel
            )
        )

        buttons.button(
            QtGui.QDialogButtonBox.Ok
        ).setText(
            "Select"
        )

        buttons.accepted.connect(
            self.select_matching_members
        )

        buttons.rejected.connect(
            self.reject
        )

        # -----------------------------------------------------
        # Main layout
        # -----------------------------------------------------

        layout = (
            QtGui.QVBoxLayout()
        )

        layout.addLayout(
            form
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            buttons
        )

        self.setLayout(
            layout
        )

    def matching_members(self):
        """Return members matching the selected tube profile."""

        return members_with_profile(
            self.members,
            self.profile_combo.currentText(),
        )

    def update_match_count(self):
        """Update the count of matching members."""

        count = len(
            self.matching_members()
        )

        if count == 1:
            text = "1 member"
        else:
            text = (
                f"{count} members"
            )

        self.match_label.setText(
            text
        )

    def select_matching_members(self):
        """Select every matching member in FreeCAD."""

        members = (
            self.matching_members()
        )

        FreeCADGui.Selection.clearSelection()

        for member in members:
            FreeCADGui.Selection.addSelection(
                member
            )

        self.accept()


class SelectMembersCommand:
    """Select generated members by tube profile."""

    def GetResources(self):
        return {
            "MenuText": "Select Members",
            "ToolTip": (
                "Select generated ForgeCAD members "
                "by tube profile"
            ),
        }

    def Activated(self):
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

        members = frame_members(
            document
        )

        if not members:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Frame Members",
                (
                    "Generate a ForgeCAD frame "
                    "before using member selection."
                ),
            )
            return

        dialog = SelectMembersDialog(
            document,
            FreeCADGui.getMainWindow(),
        )

        dialog.exec_()

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Select Members command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        SelectMembersCommand(),
    )
    