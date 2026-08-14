"""Render a simple continuous bent tube in FreeCAD."""

import FreeCAD

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.adapters.freecad.bent_tube_geometry import (
    build_bent_tube_shape,
)


document = FreeCAD.ActiveDocument

if document is None:
    document = FreeCAD.newDocument(
        "ForgeCAD_BentTube_Test"
    )


profile = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)

material = Material(
    name="A513 Type 5 DOM",
    density=7850.0,
    yield_strength=350.0,
)


tube = BentTube(
    straight_runs=(
        StraightRun(
            500.0
        ),
        StraightRun(
            750.0
        ),
    ),
    bends=(
        Bend(
            angle_degrees=90.0,
            centerline_radius=100.0,
        ),
    ),
    profile=profile,
    material=material,
)


shape, centerline = (
    build_bent_tube_shape(
        tube
    )
)


obj = document.addObject(
    "Part::Feature",
    "BentTube",
)

obj.Label = (
    "ForgeCAD Bent Tube"
)

obj.Shape = shape


obj.addProperty(
    "App::PropertyLength",
    "DevelopedLength",
    "ForgeCAD Bending",
)

obj.DevelopedLength = (
    tube.developed_length
)


obj.addProperty(
    "App::PropertyInteger",
    "BendCount",
    "ForgeCAD Bending",
)

obj.BendCount = (
    tube.bend_count
)


obj.addProperty(
    "App::PropertyLength",
    "CenterlineRadius",
    "ForgeCAD Bending",
)

obj.CenterlineRadius = (
    tube.bends[
        0
    ].centerline_radius
)


obj.addProperty(
    "App::PropertyAngle",
    "BendAngle",
    "ForgeCAD Bending",
)

obj.BendAngle = (
    tube.bends[
        0
    ].angle_degrees
)


document.recompute()


Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()


print(
    "Bent tube rendered."
)

print(
    "Developed length:",
    tube.developed_length,
)

print(
    "End point:",
    centerline.end_point,
)
