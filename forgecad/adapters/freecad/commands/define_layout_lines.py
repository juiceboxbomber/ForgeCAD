"""Define selected straight FreeCAD edges as ForgeCAD layout lines."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad import LayoutLine
from forgecad.adapters.freecad.commands.draw_layout_line import (
    create_layout_line_object,
)
from forgecad.geometry import Point3D


COMMAND_NAME = "ForgeCAD_DefineLayoutLines"


def selected_straight_edges(selection_ex):
    """Return selected straight edges with their endpoints."""

    edges = []

    for selection in selection_ex:
        for subobject in selection.SubObjects:
            if getattr(subobject, "ShapeType", None) != "Edge":
                continue

            vertices = subobject.Vertexes

            if len(vertices) != 2:
                continue

            start = vertices[0].Point
            end = vertices[1].Point

            edges.append((start, end))

    return edges


class DefineLayoutLinesCommand:
    """Convert selected straight edges into ForgeCAD layout lines."""

    def GetResources(self):
        return {
            "MenuText": "Define as Layout Lines",
            "ToolTip": (
                "Convert selected straight FreeCAD edges "
                "into ForgeCAD layout lines"
            ),
        }

    def Activated(self):
        document = FreeCAD.ActiveDocument

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Document",
                "Open or create a document first.",
            )
            return

        selected_edges = selected_straight_edges(
            FreeCADGui.Selection.getSelectionEx()
        )

        if not selected_edges:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Straight Edges Selected",
                "Select one or more straight edges first.",
            )
            return

        created_objects = []

        for start_vector, end_vector in selected_edges:
            try:
                layout_line = LayoutLine(
                    start=Point3D(
                        float(start_vector.x),
                        float(start_vector.y),
                        float(start_vector.z),
                    ),
                    end=Point3D(
                        float(end_vector.x),
                        float(end_vector.y),
                        float(end_vector.z),
                    ),
                )
            except ValueError:
                continue

            created_objects.append(
                create_layout_line_object(
                    document,
                    layout_line,
                )
            )

        document.recompute()

        FreeCADGui.Selection.clearSelection()

        for obj in created_objects:
            FreeCADGui.Selection.addSelection(obj)

        FreeCADGui.activeDocument().activeView().fitAll()

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


def register_command() -> None:
    """Register the command with FreeCAD."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        DefineLayoutLinesCommand(),
    )
    