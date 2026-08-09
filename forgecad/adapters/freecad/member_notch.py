"""FreeCAD member-notch metadata and geometry helpers."""

import FreeCAD

from forgecad.adapters.freecad.notch_geometry import (
    cope_tube_shape,
)


def ensure_notch_properties(obj):
    """Ensure a ForgeCAD member contains notch metadata."""

    if not hasattr(
        obj,
        "NotchEnabled",
    ):
        obj.addProperty(
            "App::PropertyBool",
            "NotchEnabled",
            "ForgeCAD Notch",
        )

        obj.NotchEnabled = False

    if not hasattr(
        obj,
        "NotchThroughStart",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "NotchThroughStart",
            "ForgeCAD Notch",
        )

        obj.NotchThroughStart = FreeCAD.Vector(
            0,
            0,
            0,
        )

    if not hasattr(
        obj,
        "NotchThroughEnd",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "NotchThroughEnd",
            "ForgeCAD Notch",
        )

        obj.NotchThroughEnd = FreeCAD.Vector(
            0,
            0,
            0,
        )

    if not hasattr(
        obj,
        "NotchThroughDiameter",
    ):
        obj.addProperty(
            "App::PropertyLength",
            "NotchThroughDiameter",
            "ForgeCAD Notch",
        )

        obj.NotchThroughDiameter = 0.0

    for property_name in (
        "NotchThroughStart",
        "NotchThroughEnd",
        "NotchThroughDiameter",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj


def clear_notch(
    obj,
):
    """Disable notch geometry on a member."""

    ensure_notch_properties(
        obj
    )

    obj.NotchEnabled = False

    obj.NotchThroughStart = FreeCAD.Vector(
        0,
        0,
        0,
    )

    obj.NotchThroughEnd = FreeCAD.Vector(
        0,
        0,
        0,
    )

    obj.NotchThroughDiameter = 0.0


def configure_notch(
    obj,
    through_start,
    through_end,
    through_outside_diameter,
):
    """Configure a member to cope against a through tube."""

    ensure_notch_properties(
        obj
    )

    diameter = float(
        through_outside_diameter
    )

    if diameter <= 0:
        raise ValueError(
            "Notch through diameter must be "
            "greater than zero."
        )

    obj.NotchThroughStart = FreeCAD.Vector(
        through_start.x,
        through_start.y,
        through_start.z,
    )

    obj.NotchThroughEnd = FreeCAD.Vector(
        through_end.x,
        through_end.y,
        through_end.z,
    )

    obj.NotchThroughDiameter = (
        diameter
    )

    obj.NotchEnabled = True


def build_member_shape(
    obj,
    profile,
    plain_shape_builder,
):
    """
    Build either a plain or coped ForgeCAD member shape.

    The normal tube builder is supplied by member_object.py
    so the modules remain independent.
    """

    ensure_notch_properties(
        obj
    )

    if not bool(
        obj.NotchEnabled
    ):
        return plain_shape_builder(
            obj.StartPoint,
            obj.EndPoint,
            profile,
        )

    diameter = float(
        obj.NotchThroughDiameter
    )

    if diameter <= 0:
        return plain_shape_builder(
            obj.StartPoint,
            obj.EndPoint,
            profile,
        )

    return cope_tube_shape(
        branch_start=obj.StartPoint,
        branch_end=obj.EndPoint,
        branch_profile=profile,
        through_start=obj.NotchThroughStart,
        through_end=obj.NotchThroughEnd,
        through_outside_diameter=diameter,
        plain_shape_builder=plain_shape_builder,
    )
