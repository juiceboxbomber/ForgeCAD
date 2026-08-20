"""Create and live-edit a parametric ForgeCAD bent tube in FreeCAD."""

import FreeCAD

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.adapters.freecad.bent_tube_object import (
    create_bent_tube_object,
)


document = FreeCAD.ActiveDocument

if document is None:
    document = FreeCAD.newDocument(
        "ForgeCAD_BentTube_Object_Test"
    )


existing = document.getObject(
    "ForgeCADBentTubeObject"
)

if existing is not None:
    document.removeObject(
        existing.Name
    )
    document.recompute()


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


obj = create_bent_tube_object(
    document,
    tube,
    name="ForgeCADBentTubeObject",
)

obj.TubeName = (
    "3D Multi-Bend Test"
)

document.recompute()


Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()


print(
    "Parametric bent tube created."
)

print(
    "Try editing these properties in the Data tab:"
)

print(
    "  Run1Length"
)

print(
    "  Run2Length"
)

print(
    "  Run3Length"
)

print(
    "  Bend1Angle"
)

print(
    "  Bend1Radius"
)

print(
    "  Bend1Rotation"
)

print(
    "  Bend2Angle"
)

print(
    "  Bend2Radius"
)

print(
    "  Bend2Rotation"
)

print(
    "  TubeProfile"
)
