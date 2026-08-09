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


def selected_members():
    """Return all selected objects when every object is a ForgeCAD member."""

    selection = list(
        FreeCADGui.Selection.getSelection()
    )

    if not selection:
        return []

    if not all(
        is_forgecad_member(obj)
        for obj in selection
    ):
        return []

    return selection


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


class MultiMemberPropertiesDialog(QtGui.QDialog):
    """Edit shared properties for multiple ForgeCAD members."""

    def __init__(
        self,
        members,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.members = list(
            members
        )

        self.setWindowTitle(
            "ForgeCAD Multi-Member Properties"
        )

        self.setMinimumWidth(
            500
        )

        count_label = (
            QtGui.QLabel(
                f"Editing {len(self.members)} members"
            )
        )

        # -----------------------------------------------------
        # Selected member list
        # -----------------------------------------------------

        self.member_list = (
            QtGui.QListWidget()
        )

        for member in self.members:
            member_id = str(
                member.MemberID
            )

            member_name = str(
                member.MemberName
            ).strip()

            if member_name:
                text = (
                    f"{member_id} - "
                    f"{member_name}"
                )
            else:
                text = member_id

            self.member_list.addItem(
                text
            )

        self.member_list.setMaximumHeight(
            150
        )

        # -----------------------------------------------------
        # Tube profile selector
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

        current_profiles = {
            str(
                member.TubeProfile
            )
            for member in self.members
        }

        if len(current_profiles) == 1:
            current_profile = next(
                iter(
                    current_profiles
                )
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

        form = (
            QtGui.QFormLayout()
        )

        form.addRow(
            "Tube Profile:",
            self.tube_profile,
        )

        note = (
            QtGui.QLabel(
                "Names are not changed during multi-member editing."
            )
        )

        note.setWordWrap(
            True
        )

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

        layout = (
            QtGui.QVBoxLayout()
        )

        layout.addWidget(
            count_label
        )

        layout.addWidget(
            self.member_list
        )

        layout.addSpacing(
            8
        )

        layout.addLayout(
            form
        )

        layout.addWidget(
            note
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

    def apply_changes(self):
        """Apply one tube profile to every selected member."""

        tube_profile = (
            self.tube_profile.currentText()
        )

        documents = set()

        for member in self.members:
            if (
                str(
                    member.TubeProfile
                )
                != tube_profile
            ):
                member.TubeProfile = (
                    tube_profile
                )

            document = getattr(
                member,
                "Document",
                None,
            )

            if document is not None:
                documents.add(
                    document
                )

        for document in documents:
            document.recompute()

        self.accept()


class MemberPropertiesCommand:
    """Edit properties for one or more selected ForgeCAD members."""

    def GetResources(self):
        return {
            "MenuText": "Member Properties",
            "ToolTip": (
                "Edit one member or assign a tube profile "
                "to multiple selected ForgeCAD members"
            ),
        }

    def Activated(self):
        selection = list(
            FreeCADGui.Selection.getSelection()
        )

        if not selection:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Member Selected",
                (
                    "Select one or more generated "
                    "ForgeCAD members first."
                ),
            )
            return

        invalid_objects = [
            obj
            for obj in selection
            if not is_forgecad_member(
                obj
            )
        ]

        if invalid_objects:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                (
                    "All selected objects must be "
                    "generated ForgeCAD members."
                ),
            )
            return

        if len(selection) == 1:
            dialog = MemberPropertiesDialog(
                selection[0],
                FreeCADGui.getMainWindow(),
            )

        else:
            dialog = MultiMemberPropertiesDialog(
                selection,
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
    