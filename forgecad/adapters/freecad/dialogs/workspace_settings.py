"""Workspace Settings dialog for ForgeCAD."""

from PySide import QtGui

from forgecad.workspace_settings import (
    WorkspaceSettings,
)


class WorkspaceSettingsDialog(
    QtGui.QDialog
):
    """Edit persistent ForgeCAD workspace settings."""

    def __init__(
        self,
        settings,
        parent=None,
    ):
        super().__init__(
            parent
        )

        if not isinstance(
            settings,
            WorkspaceSettings,
        ):
            raise TypeError(
                "settings must be a WorkspaceSettings instance."
            )

        self.setWindowTitle(
            "ForgeCAD Workspace Settings"
        )
        self.setMinimumWidth(
            380
        )

        self.width_box = self._length_box(
            settings.width_mm
        )
        self.height_box = self._length_box(
            settings.height_mm
        )
        self.major_grid_box = self._length_box(
            settings.major_grid_mm
        )
        self.minor_grid_box = self._length_box(
            settings.minor_grid_mm
        )

        self.grid_visible_check = (
            QtGui.QCheckBox(
                "Show grid"
            )
        )
        self.grid_visible_check.setChecked(
            settings.grid_visible
        )

        self.snap_enabled_check = (
            QtGui.QCheckBox(
                "Enable grid snapping"
            )
        )
        self.snap_enabled_check.setChecked(
            settings.snap_enabled
        )

        form = QtGui.QFormLayout()

        form.addRow(
            "Workspace width (mm):",
            self.width_box,
        )
        form.addRow(
            "Workspace height (mm):",
            self.height_box,
        )
        form.addRow(
            "Major grid spacing (mm):",
            self.major_grid_box,
        )
        form.addRow(
            "Snap grid spacing (mm):",
            self.minor_grid_box,
        )

        form.addRow(
            "",
            self.grid_visible_check,
        )
        form.addRow(
            "",
            self.snap_enabled_check,
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

    @staticmethod
    def _length_box(
        value,
    ):
        """Return a positive millimeter input."""

        box = QtGui.QDoubleSpinBox()

        box.setRange(
            0.001,
            1_000_000.0,
        )
        box.setDecimals(
            3
        )
        box.setValue(
            float(
                value
            )
        )

        return box

    @property
    def settings(self):
        """Return validated workspace settings from the dialog."""

        return WorkspaceSettings(
            width_mm=self.width_box.value(),
            height_mm=self.height_box.value(),
            major_grid_mm=self.major_grid_box.value(),
            minor_grid_mm=self.minor_grid_box.value(),
            grid_visible=(
                self.grid_visible_check.isChecked()
            ),
            snap_enabled=(
                self.snap_enabled_check.isChecked()
            ),
        )
