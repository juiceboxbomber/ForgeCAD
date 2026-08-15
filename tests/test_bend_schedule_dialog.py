"""Tests for ForgeCAD Bend Schedule dialog data."""

import sys
import types

from forgecad.services.bend_report import (
    BendReport,
    BendReportRow,
)


class FakeSignal:
    def connect(self, callback):
        self.callback = callback


class FakeWidget:
    def __init__(self, *args, **kwargs):
        pass

    def setLayout(self, layout):
        self.layout = layout


class FakeQDialog(FakeWidget):
    def setWindowTitle(self, title):
        self.title = title

    def setMinimumWidth(self, width):
        self.minimum_width = width

    def accept(self):
        pass

    def reject(self):
        pass


class FakeLabel(FakeWidget):
    def __init__(self, text=""):
        self.text = text


class FakeTableItem:
    def __init__(self, text):
        self.text = text


class FakeTable(FakeWidget):
    def __init__(self, rows, columns):
        self.rows = rows
        self.columns = columns
        self.headers = []
        self.items = {}

    def setHorizontalHeaderLabels(self, labels):
        self.headers = list(labels)

    def setItem(self, row, column, item):
        self.items[(row, column)] = item

    def resizeColumnsToContents(self):
        pass


class FakeDialogButtonBox(FakeWidget):
    Close = 1

    def __init__(self, *args):
        self.accepted = FakeSignal()
        self.rejected = FakeSignal()


class FakeLayout:
    def __init__(self):
        self.items = []

    def addWidget(self, widget):
        self.items.append(widget)


fake_freecad = types.ModuleType("FreeCAD")
fake_part = types.ModuleType("Part")

sys.modules["FreeCAD"] = fake_freecad
sys.modules["Part"] = fake_part

fake_pyside = types.ModuleType("PySide")
fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=FakeQDialog,
    QLabel=FakeLabel,
    QTableWidget=FakeTable,
    QTableWidgetItem=FakeTableItem,
    QDialogButtonBox=FakeDialogButtonBox,
    QVBoxLayout=FakeLayout,
)

sys.modules["PySide"] = fake_pyside

sys.modules.pop(
    "forgecad.adapters.freecad.dialogs.bend_schedule",
    None,
)

from forgecad.adapters.freecad.dialogs.bend_schedule import (
    BendScheduleDialog,
)


def _report():
    return BendReport(
        tooling_name="100 mm CLR Die",
        cut_length_mm=1500.0,
        rows=(
            BendReportRow(
                bend_number=1,
                mark_position_mm=500.0,
                bend_angle_degrees=92.0,
                centerline_radius_mm=100.0,
                rotation_degrees=0.0,
            ),
            BendReportRow(
                bend_number=2,
                mark_position_mm=1157.08,
                bend_angle_degrees=47.0,
                centerline_radius_mm=100.0,
                rotation_degrees=90.0,
            ),
        ),
    )


def test_dialog_populates_schedule_table():
    dialog = BendScheduleDialog(
        _report(),
        tube_name="Main Hoop",
    )

    assert dialog.title == "Bend Schedule - Main Hoop"
    assert dialog.table.rows == 2
    assert dialog.table.columns == 5
    assert dialog.table.headers[0] == "Bend"

    assert dialog.table.items[(0, 0)].text == "1"
    assert dialog.table.items[(0, 1)].text == "500.000"
    assert dialog.table.items[(1, 4)].text == "90.000"


def test_dialog_summary_includes_tooling_and_cut_length():
    dialog = BendScheduleDialog(
        _report(),
        tube_name="Main Hoop",
    )

    assert "100 mm CLR Die" in dialog.summary_label.text
    assert "1500.000 mm" in dialog.summary_label.text
