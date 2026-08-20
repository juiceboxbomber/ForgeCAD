"""Create Bent Tube dialog for ForgeCAD."""

from PySide import QtGui

from forgecad.services import (
    create_default_tube_library,
)
from forgecad.services.bent_tube_creation import (
    BendInput,
    BentTubeInput,
)


NO_TOOLING_LABEL = "No tooling"


class BendRow:
    """Widgets for one bend plus the following straight run."""

    def __init__(
        self,
        bend_number,
        parent=None,
    ):
        self.bend_number = bend_number

        self.group = QtGui.QGroupBox(
            f"Bend {bend_number}",
            parent,
        )

        form = QtGui.QFormLayout()

        self.angle_box = QtGui.QDoubleSpinBox()
        self.angle_box.setRange(
            0.1,
            179.9,
        )
        self.angle_box.setDecimals(
            1
        )
        self.angle_box.setValue(
            90.0
        )

        self.radius_box = QtGui.QDoubleSpinBox()
        self.radius_box.setRange(
            0.001,
            1_000_000.0,
        )
        self.radius_box.setDecimals(
            3
        )
        self.radius_box.setValue(
            100.0
        )

        self.rotation_box = QtGui.QDoubleSpinBox()
        self.rotation_box.setRange(
            -3600.0,
            3600.0,
        )
        self.rotation_box.setDecimals(
            1
        )
        self.rotation_box.setValue(
            0.0
        )

        self.run_box = QtGui.QDoubleSpinBox()
        self.run_box.setRange(
            0.001,
            1_000_000.0,
        )
        self.run_box.setDecimals(
            3
        )
        self.run_box.setValue(
            500.0
        )

        form.addRow(
            "Angle (deg):",
            self.angle_box,
        )
        form.addRow(
            "CLR (mm):",
            self.radius_box,
        )
        form.addRow(
            "Rotation (deg):",
            self.rotation_box,
        )
        form.addRow(
            f"Run {bend_number + 1} (mm):",
            self.run_box,
        )

        self.group.setLayout(
            form
        )

    @property
    def bend_input(self):
        """Return the BendInput represented by this row."""

        return BendInput(
            angle_degrees=self.angle_box.value(),
            centerline_radius=self.radius_box.value(),
            rotation_degrees=self.rotation_box.value(),
        )


class CreateBentTubeDialog(
    QtGui.QDialog
):
    """Collect a user-defined bent-tube path."""

    def __init__(
        self,
        tooling_names=(),
        active_tooling_name=None,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.setWindowTitle(
            "Create Bent Tube"
        )
        self.setMinimumWidth(
            460
        )

        self.name_edit = QtGui.QLineEdit()
        self.name_edit.setText(
            "Bent Tube"
        )

        self.profile_combo = QtGui.QComboBox()

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

        self.tooling_combo = QtGui.QComboBox()
        self.tooling_combo.addItem(
            NO_TOOLING_LABEL
        )

        for name in tooling_names:
            self.tooling_combo.addItem(
                str(
                    name
                )
            )

        if (
            active_tooling_name
            and active_tooling_name
            in tuple(
                tooling_names
            )
        ):
            self.tooling_combo.setCurrentText(
                active_tooling_name
            )
        else:
            self.tooling_combo.setCurrentText(
                NO_TOOLING_LABEL
            )

        self.first_run_box = QtGui.QDoubleSpinBox()
        self.first_run_box.setRange(
            0.001,
            1_000_000.0,
        )
        self.first_run_box.setDecimals(
            3
        )
        self.first_run_box.setValue(
            500.0
        )

        header_form = QtGui.QFormLayout()
        header_form.addRow(
            "Name:",
            self.name_edit,
        )
        header_form.addRow(
            "Tube profile:",
            self.profile_combo,
        )
        header_form.addRow(
            "Tooling:",
            self.tooling_combo,
        )
        header_form.addRow(
            "Run 1 (mm):",
            self.first_run_box,
        )

        self.bend_rows = []

        self.bend_layout = QtGui.QVBoxLayout()

        self.add_bend_button = QtGui.QPushButton(
            "+ Add Bend"
        )
        self.add_bend_button.clicked.connect(
            self.add_bend
        )

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok
            | QtGui.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(
            self.accept
        )
        buttons.rejected.connect(
            self.reject
        )

        layout = QtGui.QVBoxLayout()
        layout.addLayout(
            header_form
        )
        layout.addLayout(
            self.bend_layout
        )
        layout.addWidget(
            self.add_bend_button
        )
        layout.addWidget(
            buttons
        )

        self.setLayout(
            layout
        )

        self.add_bend()

    def add_bend(
        self,
    ):
        """Append one bend and one following straight run."""

        row = BendRow(
            len(
                self.bend_rows
            )
            + 1,
            self,
        )

        self.bend_rows.append(
            row
        )
        self.bend_layout.addWidget(
            row.group
        )

    @property
    def tube_name(self) -> str:
        """Return the requested tree/object name."""

        return self.name_edit.text().strip()

    @property
    def profile_name(self) -> str:
        """Return the selected profile name."""

        return self.profile_combo.currentText()

    @property
    def tooling_name(self) -> str | None:
        """Return selected tooling name or None."""

        name = self.tooling_combo.currentText()

        if name == NO_TOOLING_LABEL:
            return None

        return name

    @property
    def definition(self) -> BentTubeInput:
        """Return validated user-entered bent-tube data."""

        run_lengths = [
            self.first_run_box.value()
        ]

        run_lengths.extend(
            row.run_box.value()
            for row in self.bend_rows
        )

        bends = tuple(
            row.bend_input
            for row in self.bend_rows
        )

        return BentTubeInput(
            name=self.tube_name,
            run_lengths=tuple(
                run_lengths
            ),
            bends=bends,
        )
