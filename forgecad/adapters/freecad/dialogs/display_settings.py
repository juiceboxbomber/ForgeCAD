"""Display Settings dialog for ForgeCAD."""

from PySide import QtGui

from forgecad.display_settings import (
    DisplaySettings,
)


def rgb_to_qcolor(
    color,
):
    """Convert normalized RGB to QColor."""

    return QtGui.QColor(
        int(round(float(color[0]) * 255.0)),
        int(round(float(color[1]) * 255.0)),
        int(round(float(color[2]) * 255.0)),
    )


def qcolor_to_rgb(
    color,
):
    """Convert QColor to normalized RGB."""

    return (
        float(color.red()) / 255.0,
        float(color.green()) / 255.0,
        float(color.blue()) / 255.0,
    )


class ColorButton(
    QtGui.QPushButton
):
    """Button that stores and edits one RGB color."""

    def __init__(
        self,
        color,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self._color = rgb_to_qcolor(
            color
        )

        self.clicked.connect(
            self.choose_color
        )

        self.update_swatch()

    def choose_color(
        self,
    ):
        """Open the system color picker."""

        chosen = (
            QtGui.QColorDialog.getColor(
                self._color,
                self,
                "Choose Color",
            )
        )

        if not chosen.isValid():
            return

        self._color = chosen
        self.update_swatch()

    def update_swatch(
        self,
    ):
        """Update button text/style from the selected color."""

        self.setText(
            "#{:02X}{:02X}{:02X}".format(
                self._color.red(),
                self._color.green(),
                self._color.blue(),
            )
        )

        self.setStyleSheet(
            (
                "QPushButton {"
                f"background-color: {self.text()};"
                "min-width: 90px;"
                "}"
            )
        )

    @property
    def color(self):
        """Return normalized RGB color."""

        return qcolor_to_rgb(
            self._color
        )


class DisplaySettingsDialog(
    QtGui.QDialog
):
    """Edit ForgeCAD display styling."""

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
            DisplaySettings,
        ):
            raise TypeError(
                "settings must be a DisplaySettings instance."
            )

        self.setWindowTitle(
            "ForgeCAD Display Settings"
        )
        self.setMinimumWidth(
            420
        )

        self.grid_color_button = ColorButton(
            settings.grid_color,
            self,
        )
        self.axis_color_button = ColorButton(
            settings.axis_color,
            self,
        )
        self.layout_color_button = ColorButton(
            settings.layout_line_color,
            self,
        )

        self.grid_width_box = self._width_box(
            settings.grid_line_width
        )
        self.axis_width_box = self._width_box(
            settings.axis_line_width
        )
        self.layout_width_box = self._width_box(
            settings.layout_line_width
        )

        form = QtGui.QFormLayout()

        form.addRow(
            "Grid color:",
            self.grid_color_button,
        )
        form.addRow(
            "Grid line width:",
            self.grid_width_box,
        )
        form.addRow(
            "Axis color:",
            self.axis_color_button,
        )
        form.addRow(
            "Axis line width:",
            self.axis_width_box,
        )
        form.addRow(
            "Layout line color:",
            self.layout_color_button,
        )
        form.addRow(
            "Layout line width:",
            self.layout_width_box,
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
            form
        )
        layout.addWidget(
            buttons
        )

        self.setLayout(
            layout
        )

    @staticmethod
    def _width_box(
        value,
    ):
        """Return a positive line-width control."""

        box = QtGui.QDoubleSpinBox()
        box.setRange(
            0.1,
            20.0,
        )
        box.setDecimals(
            1
        )
        box.setSingleStep(
            0.5
        )
        box.setValue(
            float(value)
        )

        return box

    @property
    def settings(self):
        """Return validated display settings from the dialog."""

        return DisplaySettings(
            grid_color=self.grid_color_button.color,
            grid_line_width=self.grid_width_box.value(),
            axis_color=self.axis_color_button.color,
            axis_line_width=self.axis_width_box.value(),
            layout_line_color=self.layout_color_button.color,
            layout_line_width=self.layout_width_box.value(),
        )
