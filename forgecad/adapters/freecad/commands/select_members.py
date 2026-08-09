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


def members_with_name_prefix(
    members,
    prefix,
):
    """Return members whose names start with the requested prefix."""

    cleaned_prefix = (
        str(prefix).strip()
    )

    if not cleaned_prefix:
        return []

    normalized_prefix = (
        cleaned_prefix.lower()
    )

    matches = []

    for member in members:
        member_name = str(
            getattr(
                member,
                "MemberName",
                "",
            )
        ).strip()

        if member_name.lower().startswith(
            normalized_prefix
        ):
            matches.append(
                member
            )

    return matches


def members_with_material(
    members,
    material_name,
):
    """Return members using the requested material."""

    cleaned_material = (
        str(material_name).strip()
    )

    if not cleaned_material:
        return []

    normalized_material = (
        cleaned_material.lower()
    )

    matches = []

    for member in members:
        member_material = str(
            getattr(
                member,
                "Material",
                "",
            )
        ).strip()

        if (
            member_material.lower()
            == normalized_material
        ):
            matches.append(
                member
            )

    return matches


def members_with_length_range(
    members,
    minimum_length,
    maximum_length,
):
    """Return members whose lengths fall inside the range."""

    minimum = float(
        minimum_length
    )

    maximum = float(
        maximum_length
    )

    if minimum > maximum:
        minimum, maximum = (
            maximum,
            minimum,
        )

    matches = []

    for member in members:
        if not hasattr(
            member,
            "MemberLength",
        ):
            continue

        length = float(
            member.MemberLength
        )

        if (
            minimum
            <= length
            <= maximum
        ):
            matches.append(
                member
            )

    return matches


def available_materials(
    members,
):
    """Return unique non-empty material names in member order."""

    materials = []

    seen = set()

    for member in members:
        material_name = str(
            getattr(
                member,
                "Material",
                "",
            )
        ).strip()

        if not material_name:
            continue

        normalized_name = (
            material_name.lower()
        )

        if normalized_name in seen:
            continue

        seen.add(
            normalized_name
        )

        materials.append(
            material_name
        )

    return materials


class SelectMembersDialog(QtGui.QDialog):
    """Select generated ForgeCAD members by properties."""

    FILTER_PROFILE = "Tube Profile"
    FILTER_NAME_PREFIX = "Name Prefix"
    FILTER_MATERIAL = "Material"
    FILTER_LENGTH_RANGE = "Length Range"

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
            460
        )

        # -----------------------------------------------------
        # Filter type
        # -----------------------------------------------------

        self.filter_type = (
            QtGui.QComboBox()
        )

        self.filter_type.addItem(
            self.FILTER_PROFILE
        )

        self.filter_type.addItem(
            self.FILTER_NAME_PREFIX
        )

        self.filter_type.addItem(
            self.FILTER_MATERIAL
        )

        self.filter_type.addItem(
            self.FILTER_LENGTH_RANGE
        )

        # -----------------------------------------------------
        # Tube profile selector
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
        # Name prefix input
        # -----------------------------------------------------

        self.name_prefix = (
            QtGui.QLineEdit()
        )

        self.name_prefix.setPlaceholderText(
            "Example: Crossmember"
        )

        # -----------------------------------------------------
        # Material selector
        # -----------------------------------------------------

        self.material_combo = (
            QtGui.QComboBox()
        )

        for material_name in available_materials(
            self.members
        ):
            self.material_combo.addItem(
                material_name
            )

        # -----------------------------------------------------
        # Length range
        # -----------------------------------------------------

        self.minimum_length = (
            QtGui.QDoubleSpinBox()
        )

        self.minimum_length.setRange(
            0.0,
            1_000_000.0,
        )

        self.minimum_length.setDecimals(
            2
        )

        self.minimum_length.setSuffix(
            " mm"
        )

        self.minimum_length.setValue(
            0.0
        )

        self.maximum_length = (
            QtGui.QDoubleSpinBox()
        )

        self.maximum_length.setRange(
            0.0,
            1_000_000.0,
        )

        self.maximum_length.setDecimals(
            2
        )

        self.maximum_length.setSuffix(
            " mm"
        )

        longest_member = max(
            (
                float(
                    getattr(
                        member,
                        "MemberLength",
                        0.0,
                    )
                )
                for member in self.members
            ),
            default=0.0,
        )

        self.maximum_length.setValue(
            longest_member
        )

        # -----------------------------------------------------
        # Input stack
        # -----------------------------------------------------

        self.filter_stack = (
            QtGui.QStackedWidget()
        )

        # Profile page

        profile_widget = (
            QtGui.QWidget()
        )

        profile_layout = (
            QtGui.QHBoxLayout()
        )

        profile_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        profile_layout.addWidget(
            self.profile_combo
        )

        profile_widget.setLayout(
            profile_layout
        )

        # Name page

        name_widget = (
            QtGui.QWidget()
        )

        name_layout = (
            QtGui.QHBoxLayout()
        )

        name_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        name_layout.addWidget(
            self.name_prefix
        )

        name_widget.setLayout(
            name_layout
        )

        # Material page

        material_widget = (
            QtGui.QWidget()
        )

        material_layout = (
            QtGui.QHBoxLayout()
        )

        material_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        material_layout.addWidget(
            self.material_combo
        )

        material_widget.setLayout(
            material_layout
        )

        # Length page

        length_widget = (
            QtGui.QWidget()
        )

        length_layout = (
            QtGui.QHBoxLayout()
        )

        length_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        length_layout.addWidget(
            QtGui.QLabel(
                "Min:"
            )
        )

        length_layout.addWidget(
            self.minimum_length
        )

        length_layout.addWidget(
            QtGui.QLabel(
                "Max:"
            )
        )

        length_layout.addWidget(
            self.maximum_length
        )

        length_widget.setLayout(
            length_layout
        )

        self.filter_stack.addWidget(
            profile_widget
        )

        self.filter_stack.addWidget(
            name_widget
        )

        self.filter_stack.addWidget(
            material_widget
        )

        self.filter_stack.addWidget(
            length_widget
        )

        # -----------------------------------------------------
        # Match information
        # -----------------------------------------------------

        self.match_label = (
            QtGui.QLabel()
        )

        self.filter_type.currentIndexChanged.connect(
            self.filter_changed
        )

        self.profile_combo.currentIndexChanged.connect(
            self.update_match_count
        )

        self.name_prefix.textChanged.connect(
            self.update_match_count
        )

        self.material_combo.currentIndexChanged.connect(
            self.update_match_count
        )

        self.minimum_length.valueChanged.connect(
            self.update_match_count
        )

        self.maximum_length.valueChanged.connect(
            self.update_match_count
        )

        # -----------------------------------------------------
        # Form
        # -----------------------------------------------------

        form = (
            QtGui.QFormLayout()
        )

        form.addRow(
            "Filter By:",
            self.filter_type,
        )

        form.addRow(
            "Value:",
            self.filter_stack,
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

        self.filter_changed()

    def filter_changed(self):
        """Switch the visible input for the selected filter."""

        filter_name = (
            self.filter_type.currentText()
        )

        if (
            filter_name
            == self.FILTER_NAME_PREFIX
        ):
            self.filter_stack.setCurrentIndex(
                1
            )

            self.name_prefix.setFocus()

        elif (
            filter_name
            == self.FILTER_MATERIAL
        ):
            self.filter_stack.setCurrentIndex(
                2
            )

        elif (
            filter_name
            == self.FILTER_LENGTH_RANGE
        ):
            self.filter_stack.setCurrentIndex(
                3
            )

            self.minimum_length.setFocus()

        else:
            self.filter_stack.setCurrentIndex(
                0
            )

        self.update_match_count()

    def matching_members(self):
        """Return members matching the selected filter."""

        filter_name = (
            self.filter_type.currentText()
        )

        if (
            filter_name
            == self.FILTER_NAME_PREFIX
        ):
            return members_with_name_prefix(
                self.members,
                self.name_prefix.text(),
            )

        if (
            filter_name
            == self.FILTER_MATERIAL
        ):
            return members_with_material(
                self.members,
                self.material_combo.currentText(),
            )

        if (
            filter_name
            == self.FILTER_LENGTH_RANGE
        ):
            return members_with_length_range(
                self.members,
                self.minimum_length.value(),
                self.maximum_length.value(),
            )

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
    """Select generated members by ForgeCAD properties."""

    def GetResources(self):
        return {
            "MenuText": "Select Members",
            "ToolTip": (
                "Select generated ForgeCAD members "
                "by profile, name, material, or length"
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
    