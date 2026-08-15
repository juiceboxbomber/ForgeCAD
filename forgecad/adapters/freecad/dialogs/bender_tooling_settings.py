"""Bender Tooling Settings dialog for ForgeCAD."""

from PySide import QtGui

from forgecad.fabrication import (
    BendMarkReference,
    BenderLibrary,
    BenderTooling,
)


class ToolingRow:
    """Editable widgets for one bender tooling definition."""

    def __init__(self, tooling=None, parent=None):
        self.group = QtGui.QGroupBox(parent)

        self.name_edit = QtGui.QLineEdit()
        self.radius_box = QtGui.QDoubleSpinBox()
        self.reference_combo = QtGui.QComboBox()
        self.offset_box = QtGui.QDoubleSpinBox()
        self.compensation_box = QtGui.QDoubleSpinBox()
        self.remove_button = QtGui.QPushButton("Remove")

        self.radius_box.setRange(0.001, 1_000_000.0)
        self.radius_box.setDecimals(3)

        self.offset_box.setRange(-1_000_000.0, 1_000_000.0)
        self.offset_box.setDecimals(3)

        self.compensation_box.setRange(-180.0, 180.0)
        self.compensation_box.setDecimals(3)

        self.reference_combo.addItem(
            "Start tangent",
            BendMarkReference.START_TANGENT,
        )
        self.reference_combo.addItem(
            "Center of bend",
            BendMarkReference.CENTER_OF_BEND,
        )

        form = QtGui.QFormLayout()
        form.addRow("Tooling name:", self.name_edit)
        form.addRow("CLR (mm):", self.radius_box)
        form.addRow("Mark reference:", self.reference_combo)
        form.addRow("Mark offset (mm):", self.offset_box)
        form.addRow("Angle compensation (deg):", self.compensation_box)
        form.addRow("", self.remove_button)

        self.group.setLayout(form)

        if tooling is None:
            self.name_edit.setText("New Tooling")
            self.radius_box.setValue(100.0)
            self.reference_combo.setCurrentIndex(0)
            self.offset_box.setValue(0.0)
            self.compensation_box.setValue(0.0)
        else:
            self.set_tooling(tooling)

    def set_tooling(self, tooling):
        """Populate row widgets from a tooling definition."""

        self.name_edit.setText(tooling.name)
        self.radius_box.setValue(tooling.centerline_radius_mm)
        self.offset_box.setValue(tooling.mark_offset_mm)
        self.compensation_box.setValue(
            tooling.angle_compensation_degrees
        )

        index = self.reference_combo.findData(tooling.mark_reference)
        if index >= 0:
            self.reference_combo.setCurrentIndex(index)

    @property
    def tooling(self):
        """Return validated BenderTooling from the row."""

        return BenderTooling(
            name=self.name_edit.text(),
            centerline_radius_mm=self.radius_box.value(),
            mark_reference=self.reference_combo.currentData(),
            mark_offset_mm=self.offset_box.value(),
            angle_compensation_degrees=self.compensation_box.value(),
        )


class BenderToolingSettingsDialog(QtGui.QDialog):
    """Edit a project's persistent bender tooling library."""

    def __init__(self, library, parent=None):
        super().__init__(parent)

        if not isinstance(library, BenderLibrary):
            raise TypeError(
                "library must be a BenderLibrary instance."
            )

        self.setWindowTitle("ForgeCAD Bender Tooling")
        self.setMinimumWidth(500)

        self.tooling_rows = []
        self.rows_layout = QtGui.QVBoxLayout()

        self.active_combo = QtGui.QComboBox()
        self._requested_active_name = library.active_name

        for name in library.names:
            self.add_tooling_row(library.get(name))

        self.add_button = QtGui.QPushButton("+ Add Tooling")
        self.add_button.clicked.connect(
            lambda: self.add_tooling_row()
        )

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok
            | QtGui.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(self.rows_layout)
        layout.addWidget(self.add_button)

        active_form = QtGui.QFormLayout()
        active_form.addRow("Active tooling:", self.active_combo)

        layout.addLayout(active_form)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.refresh_active_combo()

        if (
            library.active_name
            and library.active_name
            in library.names
        ):
            self.active_combo.setCurrentText(
                library.active_name
            )

    def add_tooling_row(self, tooling=None):
        """Append one editable tooling row."""

        row = ToolingRow(tooling=tooling, parent=self)

        row.remove_button.clicked.connect(
            lambda checked=False, row=row: self.remove_tooling_row(row)
        )

        self.tooling_rows.append(row)
        self.rows_layout.addWidget(row.group)
        self.refresh_active_combo()

    def remove_tooling_row(self, row):
        """Remove one tooling row."""

        if row not in self.tooling_rows:
            return

        self.tooling_rows.remove(row)
        row.group.setParent(None)
        self.refresh_active_combo()

    def refresh_active_combo(self):
        """Refresh active-tooling choices from current row names."""

        current = self.active_combo.currentText()

        if not current:
            current = self._requested_active_name or ""

        self.active_combo.clear()

        names = [
            row.name_edit.text().strip()
            for row in self.tooling_rows
            if row.name_edit.text().strip()
        ]

        for name in names:
            self.active_combo.addItem(name)

        if current in names:
            self.active_combo.setCurrentText(current)
        elif names:
            self.active_combo.setCurrentIndex(0)

    @property
    def library(self):
        """Return a validated BenderLibrary from dialog values."""

        library = BenderLibrary()

        for row in self.tooling_rows:
            library.add(row.tooling)

        active_name = self.active_combo.currentText().strip()
        if active_name:
            library.set_active(active_name)

        return library
