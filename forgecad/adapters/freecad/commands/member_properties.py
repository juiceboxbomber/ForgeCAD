"""FreeCAD command for editing ForgeCAD member properties."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.services import create_default_tube_library


COMMAND_NAME = "ForgeCAD_MemberProperties"


def _quantity_value(value) -> float:
    """Return a numeric value from a FreeCAD quantity or test double."""
    return float(getattr(value, "Value", value))


def is_forgecad_straight_member(obj):
    """Return True when an object is a generated straight ForgeCAD member."""
    if obj is None:
        return False
    required_properties = (
        "MemberID",
        "MemberName",
        "TubeProfile",
        "MemberLength",
        "Material",
    )
    return all(hasattr(obj, property_name) for property_name in required_properties)


def is_forgecad_bent_member(obj):
    """Return True when an object is a parametric ForgeCAD bent member."""
    if obj is None:
        return False
    required_properties = (
        "TubeName",
        "TubeProfile",
        "Material",
        "BendCount",
        "DevelopedLength",
        "StartPoint",
        "InitialDirection",
        "InitialBendNormal",
    )
    return all(hasattr(obj, property_name) for property_name in required_properties)


def is_forgecad_member(obj):
    """Return True when an object is any ForgeCAD structural member."""
    return is_forgecad_straight_member(obj) or is_forgecad_bent_member(obj)


def member_kind(member) -> str:
    """Return a readable structural-member kind."""
    if is_forgecad_straight_member(member):
        return "Straight"
    if is_forgecad_bent_member(member):
        return "Bent"
    return "Unknown"


def member_display_name(member) -> str:
    """Return the user-facing member name."""
    if is_forgecad_straight_member(member):
        return str(member.MemberName).strip()
    if is_forgecad_bent_member(member):
        return str(member.TubeName).strip()
    return ""


def member_display_id(member) -> str:
    """Return the persistent straight-member ID when available."""
    if is_forgecad_straight_member(member):
        return str(member.MemberID).strip()
    return ""


def member_display_length(member) -> float:
    """Return the structural-member centerline length in millimeters."""
    if is_forgecad_straight_member(member):
        return _quantity_value(member.MemberLength)
    if is_forgecad_bent_member(member):
        return _quantity_value(member.DevelopedLength)
    raise ValueError("Object is not a ForgeCAD structural member.")


def set_member_display_name(member, name):
    """Set the appropriate user-facing name property."""
    cleaned_name = str(name).strip()
    if is_forgecad_straight_member(member):
        member.MemberName = cleaned_name
        return
    if is_forgecad_bent_member(member):
        member.TubeName = cleaned_name
        return
    raise ValueError("Object is not a ForgeCAD structural member.")


def selected_member():
    """Return the single selected ForgeCAD structural member."""
    selection = FreeCADGui.Selection.getSelection()
    if len(selection) != 1:
        return None
    obj = selection[0]
    if not is_forgecad_member(obj):
        return None
    return obj


def selected_members():
    """Return selection when every object is a structural member."""
    selection = list(FreeCADGui.Selection.getSelection())
    if not selection:
        return []
    if not all(is_forgecad_member(obj) for obj in selection):
        return []
    return selection


def build_bulk_member_names(members, prefix, start_number=1):
    """Return sequential names for the supplied members."""
    cleaned_prefix = str(prefix).strip()
    if not cleaned_prefix:
        return []
    return [
        (member, f"{cleaned_prefix} {start_number + index}")
        for index, member in enumerate(members)
    ]


def member_list_text(member):
    """Return one readable line for a selected structural member."""
    member_id = member_display_id(member)
    member_name = member_display_name(member)
    if member_id and member_name:
        return f"{member_id} - {member_name}"
    if member_id:
        return member_id
    if member_name:
        return f"Bent - {member_name}"
    return member_kind(member)


class MemberPropertiesDialog(QtGui.QDialog):
    """Edit the user-facing properties of one structural member."""

    def __init__(self, member, parent=None):
        super().__init__(parent)
        self.member = member
        self.setWindowTitle("ForgeCAD Member Properties")
        self.setMinimumWidth(440)

        self.member_type = QtGui.QLineEdit()
        self.member_type.setText(member_kind(member))
        self.member_type.setReadOnly(True)

        self.member_id = QtGui.QLineEdit()
        member_id = member_display_id(member)
        self.member_id.setText(member_id if member_id else "—")
        self.member_id.setReadOnly(True)

        self.member_name = QtGui.QLineEdit()
        self.member_name.setText(member_display_name(member))
        if is_forgecad_bent_member(member):
            self.member_name.setPlaceholderText("Example: Main Hoop")
        else:
            self.member_name.setPlaceholderText("Example: Front Crossmember")

        self.tube_profile = QtGui.QComboBox()
        library = create_default_tube_library()
        for profile_name in library.names:
            self.tube_profile.addItem(profile_name)
        current_profile = str(member.TubeProfile)
        profile_index = self.tube_profile.findText(current_profile)
        if profile_index >= 0:
            self.tube_profile.setCurrentIndex(profile_index)

        self.material = QtGui.QLineEdit()
        self.material.setText(str(member.Material))
        self.material.setReadOnly(True)

        self.member_length = QtGui.QLineEdit()
        length_mm = member_display_length(member)
        self.member_length.setText(f"{length_mm:.2f} mm")
        self.member_length.setReadOnly(True)

        form = QtGui.QFormLayout()
        form.addRow("Type:", self.member_type)
        form.addRow("Member ID:", self.member_id)
        form.addRow("Name:", self.member_name)
        form.addRow("Tube Profile:", self.tube_profile)
        form.addRow("Material:", self.material)
        length_label = "Developed Length:" if is_forgecad_bent_member(member) else "Length:"
        form.addRow(length_label, self.member_length)

        if is_forgecad_bent_member(member):
            self.bend_count = QtGui.QLineEdit()
            self.bend_count.setText(str(int(member.BendCount)))
            self.bend_count.setReadOnly(True)
            form.addRow("Bend Count:", self.bend_count)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )
        buttons.button(QtGui.QDialogButtonBox.Ok).setText("Apply")
        buttons.accepted.connect(self.apply_changes)
        buttons.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(form)
        layout.addSpacing(10)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.member_name.setFocus()

    def apply_changes(self):
        """Apply editable properties to the selected member."""
        member_name = self.member_name.text().strip()
        tube_profile = self.tube_profile.currentText()

        if member_display_name(self.member) != member_name:
            set_member_display_name(self.member, member_name)

        if str(self.member.TubeProfile) != tube_profile:
            self.member.TubeProfile = tube_profile

        document = getattr(self.member, "Document", None)
        if document is not None:
            document.recompute()

        self.accept()


class MultiMemberPropertiesDialog(QtGui.QDialog):
    """Edit shared properties for multiple ForgeCAD structural members."""

    def __init__(self, members, parent=None):
        super().__init__(parent)
        self.members = list(members)
        self.setWindowTitle("ForgeCAD Multi-Member Properties")
        self.setMinimumWidth(520)

        count_label = QtGui.QLabel(f"Editing {len(self.members)} members")
        self.member_list = QtGui.QListWidget()
        for member in self.members:
            self.member_list.addItem(member_list_text(member))
        self.member_list.setMaximumHeight(150)

        self.tube_profile = QtGui.QComboBox()
        library = create_default_tube_library()
        for profile_name in library.names:
            self.tube_profile.addItem(profile_name)

        current_profiles = {str(member.TubeProfile) for member in self.members}
        if len(current_profiles) == 1:
            current_profile = next(iter(current_profiles))
            profile_index = self.tube_profile.findText(current_profile)
            if profile_index >= 0:
                self.tube_profile.setCurrentIndex(profile_index)

        self.rename_members = QtGui.QCheckBox("Rename selected members")
        self.name_prefix = QtGui.QLineEdit()
        self.name_prefix.setPlaceholderText("Example: Crossmember")
        self.name_prefix.setEnabled(False)

        self.start_number = QtGui.QSpinBox()
        self.start_number.setRange(1, 9999)
        self.start_number.setValue(1)
        self.start_number.setEnabled(False)

        self.rename_members.toggled.connect(self.name_prefix.setEnabled)
        self.rename_members.toggled.connect(self.start_number.setEnabled)

        form = QtGui.QFormLayout()
        form.addRow("Tube Profile:", self.tube_profile)
        form.addRow("", self.rename_members)
        form.addRow("Name Prefix:", self.name_prefix)
        form.addRow("Start Number:", self.start_number)

        note = QtGui.QLabel("Members are named in the order they were selected.")
        note.setWordWrap(True)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )
        buttons.button(QtGui.QDialogButtonBox.Ok).setText("Apply")
        buttons.accepted.connect(self.apply_changes)
        buttons.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(count_label)
        layout.addWidget(self.member_list)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addSpacing(10)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def apply_changes(self):
        """Apply shared properties to selected structural members."""
        tube_profile = self.tube_profile.currentText()
        documents = set()

        for member in self.members:
            if str(member.TubeProfile) != tube_profile:
                member.TubeProfile = tube_profile

            document = getattr(member, "Document", None)
            if document is not None:
                documents.add(document)

        if self.rename_members.isChecked():
            prefix = self.name_prefix.text().strip()
            if not prefix:
                QtGui.QMessageBox.warning(
                    self,
                    "Name Prefix Required",
                    "Enter a name prefix before renaming the selected members.",
                )
                return

            assignments = build_bulk_member_names(
                self.members,
                prefix,
                self.start_number.value(),
            )

            for member, member_name in assignments:
                if member_display_name(member) != member_name:
                    set_member_display_name(member, member_name)

        for document in documents:
            document.recompute()

        self.accept()


class MemberPropertiesCommand:
    """Edit properties for one or more selected structural members."""

    def GetResources(self):
        return {
            "MenuText": "Member Properties",
            "ToolTip": (
                "Edit one member or bulk edit selected ForgeCAD structural members"
            ),
        }

    def Activated(self):
        selection = list(FreeCADGui.Selection.getSelection())

        if not selection:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Member Selected",
                "Select one or more generated ForgeCAD members first.",
            )
            return

        invalid_objects = [obj for obj in selection if not is_forgecad_member(obj)]

        if invalid_objects:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                "All selected objects must be ForgeCAD structural members.",
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
        return FreeCAD.ActiveDocument is not None


def register_command() -> None:
    """Register the Member Properties command."""
    FreeCADGui.addCommand(
        COMMAND_NAME,
        MemberPropertiesCommand(),
    )
