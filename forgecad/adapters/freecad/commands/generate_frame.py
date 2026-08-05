"""Generate a ForgeCAD frame from a layout."""

import FreeCAD
import FreeCADGui

from forgecad import FrameLayout, LayoutLine
from forgecad.geometry import Point3D
from forgecad.adapters.freecad import FrameRenderer
from forgecad.services import (
    build_frame_from_layout,
    create_project,
)

COMMAND_NAME = "ForgeCAD_GenerateFrame"


class GenerateFrameCommand:

    def GetResources(self):
        return {
            "MenuText": "Generate Sample Frame",
            "ToolTip": "Generate a frame from a FrameLayout",
        }

    def Activated(self):

        project = create_project("Sample Layout")

        layout = FrameLayout()

        a = Point3D(0, 0, 0)
        b = Point3D(1000, 0, 0)
        c = Point3D(1000, 600, 0)
        d = Point3D(0, 600, 0)

        layout.add_line(LayoutLine(a, b))
        layout.add_line(LayoutLine(b, c))
        layout.add_line(LayoutLine(c, d))
        layout.add_line(LayoutLine(d, a))

        frame = build_frame_from_layout(
            project,
            layout,
        )

        document = FreeCAD.newDocument("Generated Frame")

        FrameRenderer().render_frame(
            document,
            frame,
        )

        FreeCADGui.activeDocument().activeView().viewAxonometric()
        FreeCADGui.activeDocument().activeView().fitAll()

    def IsActive(self):
        return True


def register_command():

    FreeCADGui.addCommand(
        COMMAND_NAME,
        GenerateFrameCommand(),
    )
    