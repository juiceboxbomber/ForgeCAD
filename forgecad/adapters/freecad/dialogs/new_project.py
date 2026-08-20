"""New ForgeCAD project dialog."""

from PySide import QtGui

from forgecad import (
    ApplicationType,
    DisplayUnits,
    ProjectType,
)
from forgecad.services import (
    create_default_tube_library,
)


class NewProjectDialog(QtGui.QDialog):
    """Collect initial settings for a ForgeCAD project."""

    def __init__(self, parent=None):
        super().__init__(
            parent
        )

        self.setWindowTitle(
            "New ForgeCAD Project"
        )
        self.setMinimumWidth(
            420
        )

        self.name_edit = (
            QtGui.QLineEdit()
        )
        self.name_edit.setText(
            "New Project"
        )

        self.project_type_combo = (
            QtGui.QComboBox()
        )
        self.project_type_combo.addItem(
            "General Fabrication",
            ProjectType.GENERAL_FABRICATION,
        )
        self.project_type_combo.addItem(
            "Chassis",
            ProjectType.CHASSIS,
        )
        self.project_type_combo.addItem(
            "Roll Cage",
            ProjectType.ROLL_CAGE,
        )

        self.application_combo = (
            QtGui.QComboBox()
        )
        self.application_combo.addItem(
            "General",
            ApplicationType.GENERAL,
        )
        self.application_combo.addItem(
            "Off Road",
            ApplicationType.OFF_ROAD,
        )
        self.application_combo.addItem(
            "Rock Crawler",
            ApplicationType.ROCK_CRAWLER,
        )
        self.application_combo.addItem(
            "Kart",
            ApplicationType.KART,
        )
        self.application_combo.addItem(
            "Formula SAE",
            ApplicationType.FORMULA_SAE,
        )
        self.application_combo.addItem(
            "Custom",
            ApplicationType.CUSTOM,
        )

        self.units_combo = (
            QtGui.QComboBox()
        )
        self.units_combo.addItem(
            "Millimeters",
            DisplayUnits.MILLIMETERS,
        )
        self.units_combo.addItem(
            "Inches",
            DisplayUnits.INCHES,
        )

        self.profile_combo = (
            QtGui.QComboBox()
        )

        library = (
            create_default_tube_library()
        )

        for name in library.names:
            self.profile_combo.addItem(
                name
            )

        self.profile_combo.setCurrentText(
            library.active_name
        )

        form = QtGui.QFormLayout()
        form.addRow(
            "Project name:",
            self.name_edit,
        )
        form.addRow(
            "Project type:",
            self.project_type_combo,
        )
        form.addRow(
            "Application:",
            self.application_combo,
        )
        form.addRow(
            "Display units:",
            self.units_combo,
        )
        form.addRow(
            "Default tube:",
            self.profile_combo,
        )

        buttons = (
            QtGui.QDialogButtonBox(
                QtGui.QDialogButtonBox.Ok
                | QtGui.QDialogButtonBox.Cancel
            )
        )
        buttons.accepted.connect(
            self.accept
        )
        buttons.rejected.connect(
            self.reject
        )

        layout = QtGui.QVBoxLayout()
        layout.addLayout(
            form
        )
        layout.addWidget(
            buttons
        )

        self.setLayout(
            layout
        )

    @property
    def project_name(self) -> str:
        return (
            self.name_edit
            .text()
            .strip()
        )

    @property
    def project_type(self) -> ProjectType:
        return (
            self.project_type_combo
            .currentData()
        )

    @property
    def application(self) -> ApplicationType:
        return (
            self.application_combo
            .currentData()
        )

    @property
    def display_units(self) -> DisplayUnits:
        return (
            self.units_combo
            .currentData()
        )

    @property
    def active_profile_name(self) -> str:
        return (
            self.profile_combo
            .currentText()
        )
