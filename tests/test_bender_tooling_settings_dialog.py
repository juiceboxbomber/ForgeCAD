"""Tests for ForgeCAD Bender Tooling Settings dialog data."""

import sys
import types

from forgecad.fabrication import (
    BendMarkReference,
    BenderLibrary,
    BenderTooling,
)


class FakeSignal:
    def connect(self, callback):
        self.callback = callback


class FakeWidget:
    def __init__(self, *args, **kwargs):
        self.clicked = FakeSignal()

    def setLayout(self, layout):
        self.layout = layout

    def setParent(self, parent):
        self.parent = parent


class FakeQDialog(FakeWidget):
    Accepted = 1

    def setWindowTitle(self, title):
        self.title = title

    def setMinimumWidth(self, width):
        self.minimum_width = width

    def accept(self):
        pass

    def reject(self):
        pass


class FakeLineEdit(FakeWidget):
    def __init__(self):
        super().__init__()
        self._text = ""

    def setText(self, text):
        self._text = str(text)

    def text(self):
        return self._text


class FakeComboBox(FakeWidget):
    def __init__(self):
        super().__init__()
        self.items = []
        self.data = []
        self.index = -1

    def addItem(self, text, data=None):
        self.items.append(str(text))
        self.data.append(data)
        if self.index < 0:
            self.index = 0

    def clear(self):
        self.items = []
        self.data = []
        self.index = -1

    def currentText(self):
        if self.index < 0:
            return ""
        return self.items[self.index]

    def currentData(self):
        if self.index < 0:
            return None
        return self.data[self.index]

    def setCurrentText(self, text):
        if text in self.items:
            self.index = self.items.index(text)

    def setCurrentIndex(self, index):
        self.index = int(index)

    def findData(self, data):
        try:
            return self.data.index(data)
        except ValueError:
            return -1


class FakeDoubleSpinBox(FakeWidget):
    def __init__(self):
        super().__init__()
        self._value = 0.0

    def setRange(self, minimum, maximum):
        pass

    def setDecimals(self, decimals):
        pass

    def setValue(self, value):
        self._value = float(value)

    def value(self):
        return self._value


class FakeLayout:
    def __init__(self):
        self.items = []

    def addRow(self, *args):
        self.items.append(args)

    def addLayout(self, layout):
        self.items.append(layout)

    def addWidget(self, widget):
        self.items.append(widget)


class FakeDialogButtonBox(FakeWidget):
    Ok = 1
    Cancel = 2

    def __init__(self, *args):
        super().__init__()
        self.accepted = FakeSignal()
        self.rejected = FakeSignal()


fake_freecad = types.ModuleType("FreeCAD")
fake_part = types.ModuleType("Part")

sys.modules["FreeCAD"] = fake_freecad
sys.modules["Part"] = fake_part

fake_pyside = types.ModuleType("PySide")
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

sys.modules["PySide"] = fake_pyside

sys.modules.pop(
    "forgecad.adapters.freecad.dialogs.bender_tooling_settings",
    None,
)

from forgecad.adapters.freecad.dialogs.bender_tooling_settings import (
    BenderToolingSettingsDialog,
)


def _library():
    library = BenderLibrary()

    library.add(
        BenderTooling(
            name="100 mm CLR",
            centerline_radius_mm=100.0,
            mark_reference=BendMarkReference.START_TANGENT,
            mark_offset_mm=5.0,
            angle_compensation_degrees=2.0,
        )
    )

    library.add(
        BenderTooling(
            name="150 mm CLR",
            centerline_radius_mm=150.0,
            mark_reference=BendMarkReference.CENTER_OF_BEND,
            mark_offset_mm=-3.0,
            angle_compensation_degrees=1.0,
        )
    )

    library.set_active("150 mm CLR")

    return library


def test_dialog_loads_existing_tooling():
    dialog = BenderToolingSettingsDialog(_library())

    assert len(dialog.tooling_rows) == 2
    assert dialog.tooling_rows[0].tooling.name == "100 mm CLR"


def test_dialog_preserves_active_tooling():
    dialog = BenderToolingSettingsDialog(_library())

    assert dialog.active_combo.currentText() == "150 mm CLR"


def test_dialog_builds_edited_library():
    dialog = BenderToolingSettingsDialog(_library())

    dialog.tooling_rows[0].offset_box.setValue(7.5)

    result = dialog.library

    assert result.names == (
        "100 mm CLR",
        "150 mm CLR",
    )
    assert result.get("100 mm CLR").mark_offset_mm == 7.5


def test_dialog_can_add_and_remove_tooling():
    dialog = BenderToolingSettingsDialog(
        BenderLibrary()
    )

    dialog.add_tooling_row()

    assert len(dialog.tooling_rows) == 1

    row = dialog.tooling_rows[0]
    dialog.remove_tooling_row(row)

    assert dialog.tooling_rows == []
