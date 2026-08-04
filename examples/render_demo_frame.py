import sys

REPOSITORY_ROOT = r"C:\Users\user\ForgeCAD"

if REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, REPOSITORY_ROOT)

import FreeCAD

from forgecad.adapters.freecad import FrameRenderer
from forgecad.fabrication import (
    Frame,
    Material,
    Member,
    Node,
    TubeProfile,
)


doc = FreeCAD.newDocument("ForgeCAD_Demo_Frame")

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

renderer = FrameRenderer()
renderer.render_frame(doc, frame)

doc.recompute()

Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
