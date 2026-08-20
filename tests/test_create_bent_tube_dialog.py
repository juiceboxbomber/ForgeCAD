"""Tests for Create Bent Tube dialog data extraction."""

import sys
import types


# ---------------------------------------------------------
# Stub FreeCAD / Part / PySide before importing adapters.
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = fake_freecad_gui

sys.modules[
    "Part"
] = fake_part


class FakeSignal:
    def connect(
        self,
        callback,
    ):
        self.callback = callback


class FakeWidget:
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self.clicked = FakeSignal()

    def setLayout(
        self,
        layout,
    ):
        self.layout = layout


class FakeQDialog(
    FakeWidget
):
    Accepted = 1

    def setWindowTitle(
        self,
        title,
    ):
        self.title = title

    def setMinimumWidth(
        self,
        width,
    ):
        self.minimum_width = width

    def accept(
        self,
    ):
        pass

    def reject(
        self,
    ):
        pass


class FakeLineEdit(
    FakeWidget
):
    def __init__(
        self,
    ):
        super().__init__()
        self._text = ""

    def setText(
        self,
        text,
    ):
        self._text = text

    def text(
        self,
    ):
        return self._text


class FakeComboBox(
    FakeWidget
):
    def __init__(
        self,
    ):
        super().__init__()
        self.items = []
        self.current = ""

    def addItem(
        self,
        text,
    ):
        self.items.append(
            text
        )

        if not self.current:
            self.current = text

    def setCurrentText(
        self,
        text,
    ):
        self.current = text

    def currentText(
        self,
    ):
        return self.current


class FakeDoubleSpinBox(
    FakeWidget
):
    def __init__(
        self,
    ):
        super().__init__()
        self._value = 0.0

    def setRange(
        self,
        minimum,
        maximum,
    ):
        self.minimum = minimum
        self.maximum = maximum

    def setDecimals(
        self,
        decimals,
    ):
        self.decimals = decimals

    def setValue(
        self,
        value,
    ):
        self._value = float(
            value
        )

    def value(
        self,
    ):
        return self._value


class FakeLayout:
    def __init__(
        self,
    ):
        self.items = []

    def addRow(
        self,
        *args,
    ):
        self.items.append(
            args
        )

    def addLayout(
        self,
        layout,
    ):
        self.items.append(
            layout
        )

    def addWidget(
        self,
        widget,
    ):
        self.items.append(
            widget
        )


class FakeDialogButtonBox(
    FakeWidget
):
    Ok = 1
    Cancel = 2

    def __init__(
        self,
        *args,
    ):
        super().__init__()
        self.accepted = FakeSignal()
        self.rejected = FakeSignal()


fake_pyside = types.ModuleType(
    "PySide"
)

fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=FakeQDialog,
    QLineEdit=FakeLineEdit,
    QComboBox=FakeComboBox,
    QDoubleSpinBox=FakeDoubleSpinBox,
    QFormLayout=FakeLayout,
    QVBoxLayout=FakeLayout,
    QPushButton=FakeWidget,
    QGroupBox=FakeWidget,
    QDialogButtonBox=FakeDialogButtonBox,
)

sys.modules[
    "PySide"
] = fake_pyside


sys.modules.pop(
    "forgecad.adapters.freecad.dialogs.create_bent_tube",
    None,
)


from forgecad.adapters.freecad.dialogs.create_bent_tube import (
    CreateBentTubeDialog,
)


from forgecad.adapters.freecad.dialogs.create_bent_tube import (
    CreateBentTubeDialog,
)


def test_dialog_starts_with_one_bend():
    dialog = CreateBentTubeDialog()

    assert len(
        dialog.bend_rows
    ) == 1


def test_add_bend_appends_bend_and_run():
    dialog = CreateBentTubeDialog()

    dialog.add_bend()

    assert len(
        dialog.bend_rows
    ) == 2


def test_dialog_definition_builds_dynamic_path():
    dialog = CreateBentTubeDialog()

    dialog.name_edit.setText(
        "Main Hoop"
    )

    dialog.first_run_box.setValue(
        400.0
    )

    dialog.bend_rows[
        0
    ].angle_box.setValue(
        75.0
    )
    dialog.bend_rows[
        0
    ].radius_box.setValue(
        100.0
    )
    dialog.bend_rows[
        0
    ].rotation_box.setValue(
        0.0
    )
    dialog.bend_rows[
        0
    ].run_box.setValue(
        500.0
    )

    dialog.add_bend()

    dialog.bend_rows[
        1
    ].angle_box.setValue(
        45.0
    )
    dialog.bend_rows[
        1
    ].radius_box.setValue(
        125.0
    )
    dialog.bend_rows[
        1
    ].rotation_box.setValue(
        90.0
    )
    dialog.bend_rows[
        1
    ].run_box.setValue(
        600.0
    )

    definition = dialog.definition

    assert definition.name == "Main Hoop"
    assert definition.run_lengths == (
        400.0,
        500.0,
        600.0,
    )

    assert len(
        definition.bends
    ) == 2

    assert (
        definition.bends[
            1
        ].rotation_degrees
        == 90.0
    )

def test_dialog_tooling_defaults_to_none():
    dialog = CreateBentTubeDialog(
        tooling_names=(
            "100 mm CLR",
            "150 mm CLR",
        ),
    )

    assert dialog.tooling_name is None


def test_dialog_can_select_project_tooling():
    dialog = CreateBentTubeDialog(
        tooling_names=(
            "100 mm CLR",
            "150 mm CLR",
        ),
        active_tooling_name=(
            "150 mm CLR"
        ),
    )

    assert dialog.tooling_name == "150 mm CLR"
