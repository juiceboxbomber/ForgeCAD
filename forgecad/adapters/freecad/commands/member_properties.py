"""FreeCAD command for editing ForgeCAD member properties."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.services import (
    create_default_tube_library,
)


COMMAND_NAME = "ForgeCAD_MemberProperties"


def is_forgecad_member(obj):
    """Return True when an object is a generated ForgeCAD member."""

    if obj is None:
        return False

    required_properties = (
        "MemberID",
        "MemberName",
        "TubeProfile",
        "MemberLength",
        "Material",
    )

    return all(
        hasattr(
            obj,
            property_name,
        )
        for property_name
        in required_properties
    )


def selected_member():
    """Return the single selected ForgeCAD member."""

    selection = (
        FreeCADGui.Selection.getSelection()
    )

    if len(selection) != 1:
        return None

    obj = selection[0]

    if not is_forgecad_member(
        obj
    ):
        return None

    return obj


class MemberPropertiesDialog(QtGui.QDialog):
    """Edit the user-facing properties of one ForgeCAD member."""

    def __init__(
        self,
        member,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.member = member

        self.setWindowTitle(
            "ForgeCAD Member Properties"
        )

        self.setMinimumWidth(
            440
        )

        # -----------------------------------------------------
        # Member ID
        # -----------------------------------------------------

        self.member_id = (
            QtGui.QLineEdit()
        )

        self.member_id.setText(
            str(
                member.MemberID
            )
        )

        self.member_id.setReadOnly(
            True
        )

        # -----------------------------------------------------
        # Member name
        # -----------------------------------------------------

        self.member_name = (
            QtGui.QLineEdit()
        )

        self.member_name.setText(
            str(
                member.MemberName
            )
        )

        self.member_name.setPlaceholderText(
            "Example: Front Crossmember"
        )

        # -----------------------------------------------------
        # Tube profile
        # -----------------------------------------------------

        self.tube_profile = (
            QtGui.QComboBox()
        )

        library = (
            create_default_tube_library()
        )

        for profile_name in library.names:
            self.tube_profile.addItem(
                profile_name
            )

        current_profile = str(
            member.TubeProfile
        )

        profile_index = (
            self.tube_profile.findText(
                current_profile
            )
        )

        if profile_index >= 0:
            self.tube_profile.setCurrentIndex(
                profile_index
            )

        # -----------------------------------------------------
        # Material
        # -----------------------------------------------------

        self.material = (
            QtGui.QLineEdit()
        )

        self.material.setText(
            str(
                member.Material
            )
        )

        self.material.setReadOnly(
            True
        )

        # -----------------------------------------------------
        # Length
        # -----------------------------------------------------

        self.member_length = (
            QtGui.QLineEdit()
        )

        length_mm = float(
            member.MemberLength
        )

        self.member_length.setText(
            f"{length_mm:.2f} mm"
        )

        self.member_length.setReadOnly(
            True
        )

        # -----------------------------------------------------
        # Form
        # -----------------------------------------------------

        form = (
            QtGui.QFormLayout()
        )

        form.addRow(
            "Member ID:",
            self.member_id,
        )

        form.addRow(
            "Name:",
            self.member_name,
        )

        form.addRow(
            "Tube Profile:",
            self.tube_profile,
        )

        form.addRow(
            "Material:",
            self.material,
        )

        form.addRow(
            "Length:",
            self.member_length,
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
            "Apply"
        )

        buttons.accepted.connect(
            self.apply_changes
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

        self.member_name.setFocus()

    def apply_changes(self):
        """Apply editable properties to the selected member."""

        member_name = (
            self.member_name.text().strip()
        )

        tube_profile = (
            self.tube_profile.currentText()
        )

        # Assign through the FreeCAD properties rather than
        # changing the source layout object directly.
        #
        # TubeMemberProxy.onChanged() handles persistence,
        # geometry regeneration, and tree-label updates.

        if (
            str(self.member.MemberName)
            != member_name
        ):
            self.member.MemberName = (
                member_name
            )

        if (
            str(self.member.TubeProfile)
            != tube_profile
        ):
            self.member.TubeProfile = (
                tube_profile
            )

        document = (
            self.member.Document
        )

        if document is not None:
            document.recompute()

        self.accept()


class MemberPropertiesCommand:
    """Edit properties for one selected ForgeCAD member."""

    def GetResources(self):
        return {
            "MenuText": "Member Properties",
            "ToolTip": (
                "Edit the name and tube profile "
                "of the selected ForgeCAD member"
            ),
        }

    def Activated(self):
        selection = (
            FreeCADGui.Selection.getSelection()
        )

        if len(selection) == 0:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Member Selected",
                (
                    "Select one generated ForgeCAD "
                    "member first."
                ),
            )
            return

        if len(selection) > 1:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Multiple Objects Selected",
                (
                    "Select only one ForgeCAD member "
                    "for Member Properties."
                ),
            )
            return

        member = selection[0]

        if not is_forgecad_member(
            member
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                (
                    "The selected object is not a "
                    "generated ForgeCAD member."
                ),
            )
            return

        dialog = MemberPropertiesDialog(
            member,
            FreeCADGui.getMainWindow(),
        )

        dialog.exec_()

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Member Properties command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        MemberPropertiesCommand(),
    )
    