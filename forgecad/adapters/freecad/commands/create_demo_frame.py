"""FreeCAD command for creating a rectangular demonstration frame."""

import FreeCAD
import FreeCADGui

from forgecad.adapters.freecad import FrameRenderer
from forgecad.fabrication import (
    Frame,
    Material,
    Member,
    Node,
    TubeProfile,
)

COMMAND_NAME = "ForgeCAD_CreateDemoFrame"


def create_demo_frame():
    """Create and render a rectangular demonstration frame."""

    document = FreeCAD.newDocument("ForgeCAD_Demo_Frame")

    steel = Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )

    tube = TubeProfile(
        outside_diameter=31.75,
        wall_thickness=2.0,
    )

    front_left = Node(0.0, 0.0, 0.0)
    front_right = Node(1000.0, 0.0, 0.0)
    rear_right = Node(1000.0, 600.0, 0.0)
    rear_left = Node(0.0, 600.0, 0.0)

    frame = Frame()

    for node in (
        front_left,
        front_right,
        rear_right,
        rear_left,
    ):
        frame.add_node(node)

    for member in (
        Member(front_left, front_right, tube, steel),
        Member(front_right, rear_right, tube, steel),
        Member(rear_right, rear_left, tube, steel),
        Member(rear_left, front_left, tube, steel),
    ):
        frame.add_member(member)

    FrameRenderer().render_frame(document, frame)

    document.recompute()
    FreeCADGui.activeDocument().activeView().viewAxonometric()
    FreeCADGui.activeDocument().activeView().fitAll()

    return document


class CreateDemoFrameCommand:
    """FreeCAD GUI command that creates a demonstration frame."""

    def GetResources(self):
        return {
            "MenuText": "Create Demo Frame",
            "ToolTip": "Create a rectangular ForgeCAD tube frame",
        }

    def Activated(self):
        create_demo_frame()

    def IsActive(self):
        return True


def register_command() -> None:
    """Register the command with FreeCAD."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        CreateDemoFrameCommand(),
    )
    