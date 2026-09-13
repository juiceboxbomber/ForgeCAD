"""Dialog for creating a ForgeCAD reference plane."""

from PySide import QtGui

from forgecad.geometry import (
    ReferencePlane,
)


class CreateReferencePlaneDialog(
    QtGui.QDialog
):
    """Collect a name, orientation, and offset for a reference plane."""

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.setWindowTitle(
            "Create Reference Plane"
        )

        self.setMinimumWidth(
            400
        )

        self.name_edit = (
            QtGui.QLineEdit()
        )

        self.name_edit.setText(
            "Reference Plane"
        )

        self.orientation_combo = (
            QtGui.QComboBox()
        )

        self.orientation_combo.addItems(
            [
                "XY",
                "XZ",
                "YZ",
            ]
        )

        self.offset_box = (
            QtGui.QDoubleSpinBox()
        )

        self.offset_box.setRange(
            -1_000_000.0,
            1_000_000.0,
        )

        self.offset_box.setDecimals(
            3
        )

        self.offset_box.setSingleStep(
            10.0
        )

        self.offset_box.setValue(
            0.0
        )

        self.location_edit = (
            QtGui.QLineEdit()
        )

        self.location_edit.setReadOnly(
            True
        )

        self.orientation_combo.currentIndexChanged.connect(
            self.update_location
        )

        self.offset_box.valueChanged.connect(
            self.update_location
        )

        form = (
            QtGui.QFormLayout()
        )

        form.addRow(
            "Name:",
            self.name_edit,
        )

        form.addRow(
            "Orientation:",
            self.orientation_combo,
        )

        form.addRow(
            "Offset (mm):",
            self.offset_box,
        )

        form.addRow(
            "Plane Location:",
            self.location_edit,
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
            "Create Plane"
        )

        buttons.accepted.connect(
            self.accept
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

        self.update_location()

        self.name_edit.selectAll()
        self.name_edit.setFocus()

    def plane_name(
        self,
    ):
        """Return the requested plane name."""

        return str(
            self.name_edit.text()
        ).strip()

    def orientation(
        self,
    ):
        """Return the requested axis-aligned orientation."""

        return str(
            self.orientation_combo.currentText()
        ).strip()

    def offset(
        self,
    ):
        """Return the requested offset in millimeters."""

        return float(
            self.offset_box.value()
        )

    def reference_plane(
        self,
    ):
        """Return the currently requested domain reference plane."""

        return ReferencePlane(
            name=self.plane_name(),
            orientation=self.orientation(),
            offset=self.offset(),
        )

    def update_location(
        self,
        *args,
    ):
        """Show the global coordinate represented by the plane."""

        orientation = (
            self.orientation()
        )

        offset = (
            self.offset()
        )

        axis = {
            "XY": "Z",
            "XZ": "Y",
            "YZ": "X",
        }[
            orientation
        ]

        self.location_edit.setText(
            f"{axis} = {offset:.3f} mm"
        )
