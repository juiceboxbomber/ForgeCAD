"""FreeCAD member fabrication metadata and notch geometry helpers."""

import FreeCAD

from forgecad.adapters.freecad.notch_geometry import (
    cope_tube_shape,
    design_member_length,
    extended_member_endpoints,
)


def ensure_notch_properties(
    obj,
):
    """Ensure a ForgeCAD member contains fabrication metadata."""

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

    if not hasattr(
        obj,
        "StartExtension",
    ):
        obj.addProperty(
            "App::PropertyLength",
            "StartExtension",
            "ForgeCAD Fabrication",
        )

        obj.StartExtension = 0.0

    if not hasattr(
        obj,
        "EndExtension",
    ):
        obj.addProperty(
            "App::PropertyLength",
            "EndExtension",
            "ForgeCAD Fabrication",
        )

        obj.EndExtension = 0.0

    for property_name in (
        "NotchThroughStart",
        "NotchThroughEnd",
        "NotchThroughDiameter",
        "StartExtension",
        "EndExtension",
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


def clear_extensions(
    obj,
):
    """Remove fabrication extensions from both member ends."""

    ensure_notch_properties(
        obj
    )

    obj.StartExtension = 0.0
    obj.EndExtension = 0.0


def configure_start_extension(
    obj,
    extension,
):
    """Configure extra physical stock beyond the start node."""

    ensure_notch_properties(
        obj
    )

    extension = float(
        extension
    )

    if extension < 0:
        raise ValueError(
            "Start extension cannot be negative."
        )

    obj.StartExtension = (
        extension
    )


def configure_end_extension(
    obj,
    extension,
):
    """Configure extra physical stock beyond the end node."""

    ensure_notch_properties(
        obj
    )

    extension = float(
        extension
    )

    if extension < 0:
        raise ValueError(
            "End extension cannot be negative."
        )

    obj.EndExtension = (
        extension
    )


def configure_notch(
    obj,
    through_start,
    through_end,
    through_outside_diameter,
):
    """Configure a member to cope against a target tube."""

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


def physical_member_endpoints(
    obj,
):
    """Return physical endpoints including fabrication extension."""

    ensure_notch_properties(
        obj
    )

    return extended_member_endpoints(
        obj.StartPoint,
        obj.EndPoint,
        start_extension=(
            float(
                obj.StartExtension
            )
        ),
        end_extension=(
            float(
                obj.EndExtension
            )
        ),
    )


def build_member_shape(
    obj,
    profile,
    plain_shape_builder,
):
    """
    Build either a plain or coped ForgeCAD member shape.

    StartPoint and EndPoint remain the design centerline geometry.
    StartExtension and EndExtension affect only the physical solid.
    """

    ensure_notch_properties(
        obj
    )

    design_length = (
        design_member_length(
            obj.StartPoint,
            obj.EndPoint,
        )
    )

    physical_start, physical_end = (
        physical_member_endpoints(
            obj
        )
    )

    if not bool(
        obj.NotchEnabled
    ):
        shape, _ = (
            plain_shape_builder(
                physical_start,
                physical_end,
                profile,
            )
        )

        return (
            shape,
            design_length,
        )

    diameter = float(
        obj.NotchThroughDiameter
    )

    if diameter <= 0:
        shape, _ = (
            plain_shape_builder(
                physical_start,
                physical_end,
                profile,
            )
        )

        return (
            shape,
            design_length,
        )

    shape, _ = cope_tube_shape(
        branch_start=physical_start,
        branch_end=physical_end,
        branch_profile=profile,
        through_start=obj.NotchThroughStart,
        through_end=obj.NotchThroughEnd,
        through_outside_diameter=diameter,
        plain_shape_builder=plain_shape_builder,
    )

    return (
        shape,
        design_length,
    )
