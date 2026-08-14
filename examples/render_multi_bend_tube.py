"""Render a multi-bend 3D ForgeCAD tube in FreeCAD."""

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
        "ForgeCAD_MultiBend_Test"
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
            500.0
        ),
        StraightRun(
            500.0
        ),
    ),
    bends=(
        Bend(
            angle_degrees=90.0,
            centerline_radius=100.0,
            rotation_degrees=0.0,
        ),
        Bend(
            angle_degrees=90.0,
            centerline_radius=100.0,
            rotation_degrees=90.0,
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


existing = document.getObject(
    "ForgeCADMultiBentTube"
)

if existing is not None:
    document.removeObject(
        existing.Name
    )
    document.recompute()


obj = document.addObject(
    "Part::Feature",
    "ForgeCADMultiBentTube",
)

obj.Label = (
    "ForgeCAD 3D Multi-Bend Tube"
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
    "App::PropertyString",
    "BendSequence",
    "ForgeCAD Bending",
)
obj.BendSequence = (
    "90 deg @ 0 deg rotation; "
    "90 deg @ 90 deg rotation"
)


document.recompute()


Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()


print(
    "3D multi-bend tube rendered."
)

print(
    "Developed length:",
    tube.developed_length,
)

print(
    "End point:",
    centerline.end_point,
)

print(
    "End direction:",
    centerline.end_direction,
)
