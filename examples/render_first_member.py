import FreeCAD

from forgecad.adapters.freecad import FrameRenderer
from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)

doc = FreeCAD.newDocument("ForgeCAD")

steel = Material(
    "Steel",
    7850,
    350,
)

tube = TubeProfile(
    31.75,
    2.0,
)

member = Member(
    Node(0, 0, 0),
    Node(1000, 0, 0),
    tube,
    steel,
)

renderer = FrameRenderer()

renderer.render_member(
    doc,
    member,
)
