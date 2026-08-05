"""Generate a tube frame from selected ForgeCAD layout lines."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.services.layout_conversion import (
    layout_from_selected_objects,
)
from forgecad import FrameLayout, LayoutLine
from forgecad.adapters.freecad import FrameRenderer
from forgecad.geometry import Point3D
from forgecad.services import (
    build_frame_from_layout,
    create_project,
)



COMMAND_NAME = "ForgeCAD_GenerateFromSelection"


class GenerateFromSelectionCommand:
    """Generate hollow tube members from selected layout lines."""

    def GetResources(self):
        return {
            "MenuText": "Generate Frame from Selection",
            "ToolTip": (
                "Convert selected ForgeCAD layout lines "
                "into hollow tube members"
            ),
        }

    def Activated(self):
        selected_objects = FreeCADGui.Selection.getSelection()

        layout = layout_from_selected_objects(selected_objects)

        if layout.line_count == 0:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Layout Lines Selected",
                "Select one or more ForgeCAD layout lines first.",
            )
            return

        project = create_project("Generated Frame")
        frame = build_frame_from_layout(project, layout)

        document = FreeCAD.ActiveDocument

        if document is None:
            document = FreeCAD.newDocument("ForgeCAD_Generated_Frame")

        renderer = FrameRenderer()
        rendered_objects = renderer.render_frame(document, frame)

        for obj in rendered_objects:
            obj.addProperty(
                "App::PropertyString",
                "SourceType",
                "ForgeCAD",
            )
            obj.SourceType = "LayoutLine"

        document.recompute()

        FreeCADGui.activeDocument().activeView().viewAxonometric()
        FreeCADGui.activeDocument().activeView().fitAll()

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


def register_command() -> None:
    """Register the command with FreeCAD."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        GenerateFromSelectionCommand(),
    )
    