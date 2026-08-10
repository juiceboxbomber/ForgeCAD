"""FreeCAD member fabrication metadata and geometry helpers."""

import FreeCAD

from forgecad.adapters.freecad.miter_geometry import (
    miter_tube_shape,
)
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

    if not hasattr(
        obj,
        "MiterEnabled",
    ):
        obj.addProperty(
            "App::PropertyBool",
            "MiterEnabled",
            "ForgeCAD Miter",
        )

        obj.MiterEnabled = False

    if not hasattr(
        obj,
        "MiterPlanePoint",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "MiterPlanePoint",
            "ForgeCAD Miter",
        )

        obj.MiterPlanePoint = FreeCAD.Vector(
            0,
            0,
            0,
        )

    if not hasattr(
        obj,
        "MiterPlaneNormal",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "MiterPlaneNormal",
            "ForgeCAD Miter",
        )

        obj.MiterPlaneNormal = FreeCAD.Vector(
            0,
            0,
            0,
        )

    if not hasattr(
        obj,
        "MiterKeepPoint",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "MiterKeepPoint",
            "ForgeCAD Miter",
        )

        obj.MiterKeepPoint = FreeCAD.Vector(
            0,
            0,
            0,
        )

    for property_name in (
        "NotchThroughStart",
        "NotchThroughEnd",
        "NotchThroughDiameter",
        "StartExtension",
        "EndExtension",
        "MiterPlanePoint",
        "MiterPlaneNormal",
        "MiterKeepPoint",
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
    """Disable cylindrical cope geometry."""

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
    """Remove fabrication extensions from both ends."""

    ensure_notch_properties(
        obj
    )

    obj.StartExtension = 0.0
    obj.EndExtension = 0.0


def clear_miter(
    obj,
):
    """Disable planar miter geometry."""

    ensure_notch_properties(
        obj
    )

    obj.MiterEnabled = False

    obj.MiterPlanePoint = FreeCAD.Vector(
        0,
        0,
        0,
    )

    obj.MiterPlaneNormal = FreeCAD.Vector(
        0,
        0,
        0,
    )

    obj.MiterKeepPoint = FreeCAD.Vector(
        0,
        0,
        0,
    )


def configure_start_extension(
    obj,
    extension,
):
    """Configure extra stock beyond the start node."""

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

    obj.StartExtension = extension


def configure_end_extension(
    obj,
    extension,
):
    """Configure extra stock beyond the end node."""

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

    obj.EndExtension = extension


def configure_notch(
    obj,
    through_start,
    through_end,
    through_outside_diameter,
):
    """Configure a cylindrical tube cope."""

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

    obj.NotchThroughDiameter = diameter
    obj.NotchEnabled = True


def configure_miter(
    obj,
    plane_point,
    plane_normal,
    keep_point,
):
    """Configure a planar miter trim."""

    ensure_notch_properties(
        obj
    )

    if plane_normal.Length <= 0:
        raise ValueError(
            "Miter plane normal cannot be zero."
        )

    obj.MiterPlanePoint = FreeCAD.Vector(
        plane_point.x,
        plane_point.y,
        plane_point.z,
    )

    obj.MiterPlaneNormal = FreeCAD.Vector(
        plane_normal.x,
        plane_normal.y,
        plane_normal.z,
    )

    obj.MiterKeepPoint = FreeCAD.Vector(
        keep_point.x,
        keep_point.y,
        keep_point.z,
    )

    obj.MiterEnabled = True


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
        start_extension=float(
            obj.StartExtension
        ),
        end_extension=float(
            obj.EndExtension
        ),
    )


def build_member_shape(
    obj,
    profile,
    plain_shape_builder,
):
    """
    Build the final fabricated member.

    Processing order:

        design centerline
        -> physical extension
        -> hollow tube
        -> cylindrical cope
        -> planar miter
    """

    ensure_notch_properties(
        obj
    )

    design_length = design_member_length(
        obj.StartPoint,
        obj.EndPoint,
    )

    physical_start, physical_end = (
        physical_member_endpoints(
            obj
        )
    )

    shape, _ = plain_shape_builder(
        physical_start,
        physical_end,
        profile,
    )

    if bool(
        obj.NotchEnabled
    ):
        diameter = float(
            obj.NotchThroughDiameter
        )

        if diameter > 0:
            shape, _ = cope_tube_shape(
                branch_start=physical_start,
                branch_end=physical_end,
                branch_profile=profile,
                through_start=obj.NotchThroughStart,
                through_end=obj.NotchThroughEnd,
                through_outside_diameter=diameter,
                plain_shape_builder=plain_shape_builder,
            )

    if bool(
        obj.MiterEnabled
    ):
        cutter_size = max(
            physical_start.distanceToPoint(
                physical_end
            ),
            float(
                profile.outside_diameter
            ),
        ) * 4.0

        shape = miter_tube_shape(
            tube_shape=shape,
            plane_point=obj.MiterPlanePoint,
            plane_normal=obj.MiterPlaneNormal,
            keep_point=obj.MiterKeepPoint,
            cutter_size=cutter_size,
        )

    return (
        shape,
        design_length,
    )
