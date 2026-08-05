"""FreeCAD command for creating a ForgeCAD layout line."""

import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui

from forgecad import LayoutLine
from forgecad.geometry import Point3D


COMMAND_NAME = "ForgeCAD_DrawLayoutLine"


class LayoutLineDialog(QtGui.QDialog):
    """Collect start and end coordinates for a layout line."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Draw Layout Line")
        self.setMinimumWidth(360)

        self.start_x = self._create_coordinate_box(0.0)
        self.start_y = self._create_coordinate_box(0.0)
        self.start_z = self._create_coordinate_box(0.0)

        self.end_x = self._create_coordinate_box(1000.0)
        self.end_y = self._create_coordinate_box(0.0)
        self.end_z = self._create_coordinate_box(0.0)

        form = QtGui.QFormLayout()
        form.addRow("Start X (mm):", self.start_x)
        form.addRow("Start Y (mm):", self.start_y)
        form.addRow("Start Z (mm):", self.start_z)
        form.addRow("End X (mm):", self.end_x)
        form.addRow("End Y (mm):", self.end_y)
        form.addRow("End Z (mm):", self.end_z)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok
            | QtGui.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.setLayout(layout)

    @staticmethod
    def _create_coordinate_box(value: float):
        box = QtGui.QDoubleSpinBox()
        box.setRange(-1_000_000.0, 1_000_000.0)
        box.setDecimals(3)
        box.setValue(value)
        return box

    @property
    def start_point(self) -> Point3D:
        return Point3D(
            self.start_x.value(),
            self.start_y.value(),
            self.start_z.value(),
        )

    @property
    def end_point(self) -> Point3D:
        return Point3D(
            self.end_x.value(),
            self.end_y.value(),
            self.end_z.value(),
        )


def create_layout_line_object(document, layout_line: LayoutLine):
    """Create a visible FreeCAD object representing a layout line."""

    start = FreeCAD.Vector(
        layout_line.start.x,
        layout_line.start.y,
        layout_line.start.z,
    )

    end = FreeCAD.Vector(
        layout_line.end.x,
        layout_line.end.y,
        layout_line.end.z,
    )

    obj = document.addObject(
        "Part::Feature",
        "ForgeCADLayoutLine",
    )
    obj.Label = "Layout Line"
    obj.Shape = Part.makeLine(start, end)

    obj.addProperty(
        "App::PropertyVector",
        "StartPoint",
        "ForgeCAD Layout",
    )
    obj.StartPoint = start

    obj.addProperty(
        "App::PropertyVector",
        "EndPoint",
        "ForgeCAD Layout",
    )
    obj.EndPoint = end

    obj.addProperty(
        "App::PropertyLength",
        "LayoutLength",
        "ForgeCAD Layout",
    )
    obj.LayoutLength = layout_line.length

    document.recompute()
    return obj


class DrawLayoutLineCommand:
    """Create a layout line from entered coordinates."""

    def GetResources(self):
        return {
            "MenuText": "Draw Layout Line",
            "ToolTip": "Create a ForgeCAD centerline between two points",
        }

    def Activated(self):
        dialog = LayoutLineDialog(
            FreeCADGui.getMainWindow(),
        )

        if dialog.exec_() != QtGui.QDialog.Accepted:
            return

        try:
            layout_line = LayoutLine(
                start=dialog.start_point,
                end=dialog.end_point,
            )
        except ValueError as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Layout Line",
                str(error),
            )
            return

        document = FreeCAD.ActiveDocument

        if document is None:
            document = FreeCAD.newDocument("ForgeCAD_Layout")

        create_layout_line_object(
            document,
            layout_line,
        )

        FreeCADGui.activeDocument().activeView().fitAll()

    def IsActive(self):
        return True


def register_command() -> None:
    """Register the Draw Layout Line command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        DrawLayoutLineCommand(),
    )
    