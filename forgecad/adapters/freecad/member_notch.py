"""FreeCAD member fabrication metadata and geometry helpers."""

import FreeCAD

from forgecad.adapters.freecad.miter_geometry import (
    miter_tube_shape,
)
from forgecad.adapters.freecad.notch_geometry import (
    build_through_tube_cutting_tool,
    cope_tube_shape,
    design_member_length,
    extended_member_endpoints,
    primary_cope_component,
    temporary_cope_extension,
)


def zero_vector():
    """Return a zero FreeCAD vector."""

    return FreeCAD.Vector(
        0,
        0,
        0,
    )


def ensure_notch_properties(
    obj,
):
    """Ensure a ForgeCAD member contains fabrication metadata."""

    # ---------------------------------------------------------
    # Legacy single cylindrical cope
    #
    # These properties are retained for compatibility with
    # documents and tests from the original single-cope model.
    # New rendering uses independent Start/End cope properties.
    # ---------------------------------------------------------

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
        obj.NotchThroughStart = zero_vector()

    if not hasattr(
        obj,
        "NotchThroughEnd",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "NotchThroughEnd",
            "ForgeCAD Notch",
        )
        obj.NotchThroughEnd = zero_vector()

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

    # ---------------------------------------------------------
    # Start-end cylindrical cope
    # ---------------------------------------------------------

    if not hasattr(
        obj,
        "StartCopeEnabled",
    ):
        obj.addProperty(
            "App::PropertyBool",
            "StartCopeEnabled",
            "ForgeCAD Start Cope",
        )
        obj.StartCopeEnabled = False

    if not hasattr(
        obj,
        "StartCopeThroughStart",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "StartCopeThroughStart",
            "ForgeCAD Start Cope",
        )
        obj.StartCopeThroughStart = zero_vector()

    if not hasattr(
        obj,
        "StartCopeThroughEnd",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "StartCopeThroughEnd",
            "ForgeCAD Start Cope",
        )
        obj.StartCopeThroughEnd = zero_vector()

    if not hasattr(
        obj,
        "StartCopeThroughDiameter",
    ):
        obj.addProperty(
            "App::PropertyLength",
            "StartCopeThroughDiameter",
            "ForgeCAD Start Cope",
        )
        obj.StartCopeThroughDiameter = 0.0

    if not hasattr(obj, "StartCopeTargetMember"):
        obj.addProperty(
            "App::PropertyLink",
            "StartCopeTargetMember",
            "ForgeCAD Start Cope",
        )
        obj.StartCopeTargetMember = None

    # ---------------------------------------------------------
    # End-end cylindrical cope
    # ---------------------------------------------------------

    if not hasattr(
        obj,
        "EndCopeEnabled",
    ):
        obj.addProperty(
            "App::PropertyBool",
            "EndCopeEnabled",
            "ForgeCAD End Cope",
        )
        obj.EndCopeEnabled = False

    if not hasattr(
        obj,
        "EndCopeThroughStart",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "EndCopeThroughStart",
            "ForgeCAD End Cope",
        )
        obj.EndCopeThroughStart = zero_vector()

    if not hasattr(
        obj,
        "EndCopeThroughEnd",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "EndCopeThroughEnd",
            "ForgeCAD End Cope",
        )
        obj.EndCopeThroughEnd = zero_vector()

    if not hasattr(
        obj,
        "EndCopeThroughDiameter",
    ):
        obj.addProperty(
            "App::PropertyLength",
            "EndCopeThroughDiameter",
            "ForgeCAD End Cope",
        )
        obj.EndCopeThroughDiameter = 0.0

    if not hasattr(obj, "EndCopeTargetMember"):
        obj.addProperty(
            "App::PropertyLink",
            "EndCopeTargetMember",
            "ForgeCAD End Cope",
        )
        obj.EndCopeTargetMember = None

    # ---------------------------------------------------------
    # Secondary start-end cylindrical cope
    # ---------------------------------------------------------

    if not hasattr(obj, "StartCope2Enabled"):
        obj.addProperty(
            "App::PropertyBool",
            "StartCope2Enabled",
            "ForgeCAD Start Cope",
        )
        obj.StartCope2Enabled = False

    if not hasattr(obj, "StartCope2ThroughStart"):
        obj.addProperty(
            "App::PropertyVector",
            "StartCope2ThroughStart",
            "ForgeCAD Start Cope",
        )
        obj.StartCope2ThroughStart = zero_vector()

    if not hasattr(obj, "StartCope2ThroughEnd"):
        obj.addProperty(
            "App::PropertyVector",
            "StartCope2ThroughEnd",
            "ForgeCAD Start Cope",
        )
        obj.StartCope2ThroughEnd = zero_vector()

    if not hasattr(obj, "StartCope2ThroughDiameter"):
        obj.addProperty(
            "App::PropertyLength",
            "StartCope2ThroughDiameter",
            "ForgeCAD Start Cope",
        )
        obj.StartCope2ThroughDiameter = 0.0

    if not hasattr(obj, "StartCope2TargetMember"):
        obj.addProperty(
            "App::PropertyLink",
            "StartCope2TargetMember",
            "ForgeCAD Start Cope",
        )
        obj.StartCope2TargetMember = None

    # ---------------------------------------------------------
    # Secondary end-end cylindrical cope
    # ---------------------------------------------------------

    if not hasattr(obj, "EndCope2Enabled"):
        obj.addProperty(
            "App::PropertyBool",
            "EndCope2Enabled",
            "ForgeCAD End Cope",
        )
        obj.EndCope2Enabled = False

    if not hasattr(obj, "EndCope2ThroughStart"):
        obj.addProperty(
            "App::PropertyVector",
            "EndCope2ThroughStart",
            "ForgeCAD End Cope",
        )
        obj.EndCope2ThroughStart = zero_vector()

    if not hasattr(obj, "EndCope2ThroughEnd"):
        obj.addProperty(
            "App::PropertyVector",
            "EndCope2ThroughEnd",
            "ForgeCAD End Cope",
        )
        obj.EndCope2ThroughEnd = zero_vector()

    if not hasattr(obj, "EndCope2ThroughDiameter"):
        obj.addProperty(
            "App::PropertyLength",
            "EndCope2ThroughDiameter",
            "ForgeCAD End Cope",
        )
        obj.EndCope2ThroughDiameter = 0.0

    if not hasattr(obj, "EndCope2TargetMember"):
        obj.addProperty(
            "App::PropertyLink",
            "EndCope2TargetMember",
            "ForgeCAD End Cope",
        )
        obj.EndCope2TargetMember = None

    # ---------------------------------------------------------
    # Tertiary start/end cylindrical cope
    # ---------------------------------------------------------
    for side in ("Start","End"):
        p=side+"Cope3"; group="ForgeCAD "+side+" Cope"
        if not hasattr(obj,p+"Enabled"):
            obj.addProperty("App::PropertyBool",p+"Enabled",group); setattr(obj,p+"Enabled",False)
        if not hasattr(obj,p+"ThroughStart"):
            obj.addProperty("App::PropertyVector",p+"ThroughStart",group); setattr(obj,p+"ThroughStart",zero_vector())
        if not hasattr(obj,p+"ThroughEnd"):
            obj.addProperty("App::PropertyVector",p+"ThroughEnd",group); setattr(obj,p+"ThroughEnd",zero_vector())
        if not hasattr(obj,p+"ThroughDiameter"):
            obj.addProperty("App::PropertyLength",p+"ThroughDiameter",group); setattr(obj,p+"ThroughDiameter",0.0)
        if not hasattr(obj,p+"TargetMember"):
            obj.addProperty("App::PropertyLink",p+"TargetMember",group); setattr(obj,p+"TargetMember",None)

    # ---------------------------------------------------------
    # Physical fabrication extension
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Start-end miter
    # ---------------------------------------------------------

    if not hasattr(
        obj,
        "StartMiterEnabled",
    ):
        obj.addProperty(
            "App::PropertyBool",
            "StartMiterEnabled",
            "ForgeCAD Start Miter",
        )
        obj.StartMiterEnabled = False

    if not hasattr(
        obj,
        "StartMiterPlanePoint",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "StartMiterPlanePoint",
            "ForgeCAD Start Miter",
        )
        obj.StartMiterPlanePoint = zero_vector()

    if not hasattr(
        obj,
        "StartMiterPlaneNormal",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "StartMiterPlaneNormal",
            "ForgeCAD Start Miter",
        )
        obj.StartMiterPlaneNormal = zero_vector()

    if not hasattr(
        obj,
        "StartMiterKeepPoint",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "StartMiterKeepPoint",
            "ForgeCAD Start Miter",
        )
        obj.StartMiterKeepPoint = zero_vector()

    # ---------------------------------------------------------
    # End-end miter
    # ---------------------------------------------------------

    if not hasattr(
        obj,
        "EndMiterEnabled",
    ):
        obj.addProperty(
            "App::PropertyBool",
            "EndMiterEnabled",
            "ForgeCAD End Miter",
        )
        obj.EndMiterEnabled = False

    if not hasattr(
        obj,
        "EndMiterPlanePoint",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "EndMiterPlanePoint",
            "ForgeCAD End Miter",
        )
        obj.EndMiterPlanePoint = zero_vector()

    if not hasattr(
        obj,
        "EndMiterPlaneNormal",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "EndMiterPlaneNormal",
            "ForgeCAD End Miter",
        )
        obj.EndMiterPlaneNormal = zero_vector()

    if not hasattr(
        obj,
        "EndMiterKeepPoint",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "EndMiterKeepPoint",
            "ForgeCAD End Miter",
        )
        obj.EndMiterKeepPoint = zero_vector()

    # ---------------------------------------------------------
    # Legacy single-miter properties
    # ---------------------------------------------------------

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
        obj.MiterPlanePoint = zero_vector()

    if not hasattr(
        obj,
        "MiterPlaneNormal",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "MiterPlaneNormal",
            "ForgeCAD Miter",
        )
        obj.MiterPlaneNormal = zero_vector()

    if not hasattr(
        obj,
        "MiterKeepPoint",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "MiterKeepPoint",
            "ForgeCAD Miter",
        )
        obj.MiterKeepPoint = zero_vector()

    for property_name in (
        "NotchThroughStart",
        "NotchThroughEnd",
        "NotchThroughDiameter",
        "StartCopeThroughStart",
        "StartCopeThroughEnd",
        "StartCopeThroughDiameter",
        "EndCopeThroughStart",
        "EndCopeThroughEnd",
        "EndCopeThroughDiameter",
        "StartCope2ThroughStart",
        "StartCope2ThroughEnd",
        "StartCope2ThroughDiameter",
        "EndCope2ThroughStart",
        "EndCope2ThroughEnd",
        "EndCope2ThroughDiameter",
        "StartCope3ThroughStart",
        "StartCope3ThroughEnd",
        "StartCope3ThroughDiameter",
        "EndCope3ThroughStart",
        "EndCope3ThroughEnd",
        "EndCope3ThroughDiameter",
        "StartExtension",
        "EndExtension",
        "StartMiterPlanePoint",
        "StartMiterPlaneNormal",
        "StartMiterKeepPoint",
        "EndMiterPlanePoint",
        "EndMiterPlaneNormal",
        "EndMiterKeepPoint",
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


def clear_start_cope(obj):
    ensure_notch_properties(obj)
    for p in ("StartCope","StartCope2","StartCope3"):
        setattr(obj,p+"Enabled",False)
        setattr(obj,p+"ThroughStart",zero_vector())
        setattr(obj,p+"ThroughEnd",zero_vector())
        setattr(obj,p+"ThroughDiameter",0.0)
        setattr(obj,p+"TargetMember",None)




def clear_end_cope(obj):
    ensure_notch_properties(obj)
    for p in ("EndCope","EndCope2","EndCope3"):
        setattr(obj,p+"Enabled",False)
        setattr(obj,p+"ThroughStart",zero_vector())
        setattr(obj,p+"ThroughEnd",zero_vector())
        setattr(obj,p+"ThroughDiameter",0.0)
        setattr(obj,p+"TargetMember",None)




def clear_notch(
    obj,
):
    """Disable all cylindrical cope geometry."""

    ensure_notch_properties(
        obj
    )

    clear_start_cope(
        obj
    )
    clear_end_cope(
        obj
    )

    obj.NotchEnabled = False
    obj.NotchThroughStart = zero_vector()
    obj.NotchThroughEnd = zero_vector()
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


def clear_start_miter(
    obj,
):
    """Disable the miter at the member start."""

    ensure_notch_properties(
        obj
    )

    obj.StartMiterEnabled = False
    obj.StartMiterPlanePoint = zero_vector()
    obj.StartMiterPlaneNormal = zero_vector()
    obj.StartMiterKeepPoint = zero_vector()


def clear_end_miter(
    obj,
):
    """Disable the miter at the member end."""

    ensure_notch_properties(
        obj
    )

    obj.EndMiterEnabled = False
    obj.EndMiterPlanePoint = zero_vector()
    obj.EndMiterPlaneNormal = zero_vector()
    obj.EndMiterKeepPoint = zero_vector()


def clear_miter(
    obj,
):
    """Disable all planar miter geometry."""

    ensure_notch_properties(
        obj
    )

    clear_start_miter(
        obj
    )
    clear_end_miter(
        obj
    )

    obj.MiterEnabled = False
    obj.MiterPlanePoint = zero_vector()
    obj.MiterPlaneNormal = zero_vector()
    obj.MiterKeepPoint = zero_vector()


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


def validate_cope_diameter(
    through_outside_diameter,
):
    """Return a validated positive cope target diameter."""

    diameter = float(
        through_outside_diameter
    )

    if diameter <= 0:
        raise ValueError(
            "Notch through diameter must be "
            "greater than zero."
        )

    return diameter


def configure_start_cope(
    obj,
    through_start,
    through_end,
    through_outside_diameter,
):
    """Configure a cylindrical cope at the member start."""

    ensure_notch_properties(
        obj
    )

    diameter = validate_cope_diameter(
        through_outside_diameter
    )

    obj.StartCopeThroughStart = FreeCAD.Vector(
        through_start.x,
        through_start.y,
        through_start.z,
    )
    obj.StartCopeThroughEnd = FreeCAD.Vector(
        through_end.x,
        through_end.y,
        through_end.z,
    )
    obj.StartCopeThroughDiameter = diameter
    obj.StartCopeEnabled = True


def configure_end_cope(
    obj,
    through_start,
    through_end,
    through_outside_diameter,
):
    """Configure a cylindrical cope at the member end."""

    ensure_notch_properties(
        obj
    )

    diameter = validate_cope_diameter(
        through_outside_diameter
    )

    obj.EndCopeThroughStart = FreeCAD.Vector(
        through_start.x,
        through_start.y,
        through_start.z,
    )
    obj.EndCopeThroughEnd = FreeCAD.Vector(
        through_end.x,
        through_end.y,
        through_end.z,
    )
    obj.EndCopeThroughDiameter = diameter
    obj.EndCopeEnabled = True


def configure_start_cope_secondary(
    obj,
    through_start,
    through_end,
    through_outside_diameter,
):
    """Configure a second cylindrical cope at the member start."""

    ensure_notch_properties(obj)
    diameter = validate_cope_diameter(through_outside_diameter)

    obj.StartCope2ThroughStart = FreeCAD.Vector(
        through_start.x,
        through_start.y,
        through_start.z,
    )
    obj.StartCope2ThroughEnd = FreeCAD.Vector(
        through_end.x,
        through_end.y,
        through_end.z,
    )
    obj.StartCope2ThroughDiameter = diameter
    obj.StartCope2Enabled = True


def configure_end_cope_secondary(
    obj,
    through_start,
    through_end,
    through_outside_diameter,
):
    """Configure a second cylindrical cope at the member end."""

    ensure_notch_properties(obj)
    diameter = validate_cope_diameter(through_outside_diameter)

    obj.EndCope2ThroughStart = FreeCAD.Vector(
        through_start.x,
        through_start.y,
        through_start.z,
    )
    obj.EndCope2ThroughEnd = FreeCAD.Vector(
        through_end.x,
        through_end.y,
        through_end.z,
    )
    obj.EndCope2ThroughDiameter = diameter
    obj.EndCope2Enabled = True


def configure_start_cope_tertiary(obj, through_start, through_end, through_outside_diameter):
    ensure_notch_properties(obj)
    diameter=validate_cope_diameter(through_outside_diameter)
    obj.StartCope3ThroughStart=FreeCAD.Vector(through_start.x,through_start.y,through_start.z)
    obj.StartCope3ThroughEnd=FreeCAD.Vector(through_end.x,through_end.y,through_end.z)
    obj.StartCope3ThroughDiameter=diameter
    obj.StartCope3Enabled=True

def configure_end_cope_tertiary(obj, through_start, through_end, through_outside_diameter):
    ensure_notch_properties(obj)
    diameter=validate_cope_diameter(through_outside_diameter)
    obj.EndCope3ThroughStart=FreeCAD.Vector(through_start.x,through_start.y,through_start.z)
    obj.EndCope3ThroughEnd=FreeCAD.Vector(through_end.x,through_end.y,through_end.z)
    obj.EndCope3ThroughDiameter=diameter
    obj.EndCope3Enabled=True

def sync_cope_axes_from_target_members(
    obj,
):
    """Refresh linked cope axes without replacing a bent tangent by its chord."""

    ensure_notch_properties(
        obj
    )

    cope_slots = (
        (
            "StartCope",
            "start",
        ),
        (
            "EndCope",
            "end",
        ),
        (
            "StartCope2",
            "start",
        ),
        (
            "EndCope2",
            "end",
        ),
        (
            "StartCope3",
            "start",
        ),
        (
            "EndCope3",
            "end",
        ),
    )

    refreshed = 0

    for (
        prefix,
        coped_end,
    ) in cope_slots:
        if not bool(
            getattr(
                obj,
                prefix
                + "Enabled",
                False,
            )
        ):
            continue

        target_member = getattr(
            obj,
            prefix
            + "TargetMember",
            None,
        )

        if target_member is None:
            continue

        bent_target = (
            not str(
                getattr(
                    target_member,
                    "SourceLayoutID",
                    "",
                )
                or ""
            ).strip()
            and (
                bool(
                    str(
                        getattr(
                            target_member,
                            "StartFabricationLayoutID",
                            "",
                        )
                        or ""
                    ).strip()
                )
                or bool(
                    str(
                        getattr(
                            target_member,
                            "EndFabricationLayoutID",
                            "",
                        )
                        or ""
                    ).strip()
                )
                or bool(
                    getattr(
                        target_member,
                        "SourceLayoutLines",
                        (),
                    )
                )
            )
        )

        if bent_target:
            # Use the same domain-level endpoint tangent already proven by
            # bent-member miter geometry. If conversion ever fails, retain the
            # last correctly configured axis rather than falling back to the
            # geometrically false bent start-to-end chord.
            try:
                from forgecad.adapters.freecad.joint_inspector_adapter import (
                    structural_member_from_freecad_object,
                )
                from forgecad.fabrication import (
                    BentMember,
                    Node,
                )
                from forgecad.services.joint_geometry import (
                    member_direction_from_node,
                )
                from forgecad.services.node_proximity import (
                    nodes_coincident,
                )

                domain_target = (
                    structural_member_from_freecad_object(
                        target_member
                    )
                )

                if not isinstance(
                    domain_target,
                    BentMember,
                ):
                    continue

                joint_point = (
                    obj.StartPoint
                    if coped_end
                    == "start"
                    else obj.EndPoint
                )

                joint_node = Node(
                    float(
                        joint_point.x
                    ),
                    float(
                        joint_point.y
                    ),
                    float(
                        joint_point.z
                    ),
                )

                (
                    dx,
                    dy,
                    dz,
                ) = member_direction_from_node(
                    domain_target,
                    joint_node,
                )

                if nodes_coincident(
                    domain_target.start,
                    joint_node,
                ):
                    run_length = float(
                        domain_target.tube.straight_runs[
                            0
                        ].length_mm
                    )

                elif nodes_coincident(
                    domain_target.end,
                    joint_node,
                ):
                    run_length = float(
                        domain_target.tube.straight_runs[
                            -1
                        ].length_mm
                    )

                else:
                    continue

                axis_length = max(
                    run_length,
                    float(
                        domain_target.profile.outside_diameter
                    ),
                    1.0,
                )

                target_start = FreeCAD.Vector(
                    float(
                        joint_point.x
                    ),
                    float(
                        joint_point.y
                    ),
                    float(
                        joint_point.z
                    ),
                )

                target_end = FreeCAD.Vector(
                    target_start.x
                    + dx
                    * axis_length,
                    target_start.y
                    + dy
                    * axis_length,
                    target_start.z
                    + dz
                    * axis_length,
                )

            except Exception:
                continue

        else:
            if (
                not hasattr(
                    target_member,
                    "StartPoint",
                )
                or not hasattr(
                    target_member,
                    "EndPoint",
                )
            ):
                continue

            target_start = (
                target_member.StartPoint
            )
            target_end = (
                target_member.EndPoint
            )

        setattr(
            obj,
            prefix
            + "ThroughStart",
            FreeCAD.Vector(
                target_start.x,
                target_start.y,
                target_start.z,
            ),
        )

        setattr(
            obj,
            prefix
            + "ThroughEnd",
            FreeCAD.Vector(
                target_end.x,
                target_end.y,
                target_end.z,
            ),
        )

        refreshed += 1

    return refreshed





def configure_notch(
    obj,
    through_start,
    through_end,
    through_outside_diameter,
):
    """
    Configure the legacy single cylindrical cope.

    New code should use configure_start_cope() or
    configure_end_cope().
    """

    ensure_notch_properties(
        obj
    )

    diameter = validate_cope_diameter(
        through_outside_diameter
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


def validate_miter_normal(
    plane_normal,
):
    """Reject a zero-length miter-plane normal."""

    if plane_normal.Length <= 0:
        raise ValueError(
            "Miter plane normal cannot be zero."
        )


def configure_start_miter(
    obj,
    plane_point,
    plane_normal,
    keep_point,
):
    """Configure a planar miter at the member start."""

    ensure_notch_properties(
        obj
    )

    validate_miter_normal(
        plane_normal
    )

    obj.StartMiterPlanePoint = FreeCAD.Vector(
        plane_point.x,
        plane_point.y,
        plane_point.z,
    )
    obj.StartMiterPlaneNormal = FreeCAD.Vector(
        plane_normal.x,
        plane_normal.y,
        plane_normal.z,
    )
    obj.StartMiterKeepPoint = FreeCAD.Vector(
        keep_point.x,
        keep_point.y,
        keep_point.z,
    )
    obj.StartMiterEnabled = True


def configure_end_miter(
    obj,
    plane_point,
    plane_normal,
    keep_point,
):
    """Configure a planar miter at the member end."""

    ensure_notch_properties(
        obj
    )

    validate_miter_normal(
        plane_normal
    )

    obj.EndMiterPlanePoint = FreeCAD.Vector(
        plane_point.x,
        plane_point.y,
        plane_point.z,
    )
    obj.EndMiterPlaneNormal = FreeCAD.Vector(
        plane_normal.x,
        plane_normal.y,
        plane_normal.z,
    )
    obj.EndMiterKeepPoint = FreeCAD.Vector(
        keep_point.x,
        keep_point.y,
        keep_point.z,
    )
    obj.EndMiterEnabled = True


def configure_miter(
    obj,
    plane_point,
    plane_normal,
    keep_point,
):
    """Compatibility helper for the original single-miter API."""

    ensure_notch_properties(
        obj
    )

    start_distance = FreeCAD.Vector(
        plane_point.x - obj.StartPoint.x,
        plane_point.y - obj.StartPoint.y,
        plane_point.z - obj.StartPoint.z,
    ).Length

    end_distance = FreeCAD.Vector(
        plane_point.x - obj.EndPoint.x,
        plane_point.y - obj.EndPoint.y,
        plane_point.z - obj.EndPoint.z,
    ).Length

    if start_distance <= end_distance:
        configure_start_miter(
            obj,
            plane_point,
            plane_normal,
            keep_point,
        )
    else:
        configure_end_miter(
            obj,
            plane_point,
            plane_normal,
            keep_point,
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


def miter_cutter_size(
    physical_start,
    physical_end,
    profile,
):
    """Return a cutter size large enough for either member end."""

    return max(
        physical_start.distanceToPoint(
            physical_end
        ),
        float(
            profile.outside_diameter
        ),
    ) * 4.0


def vector_between(
    start,
    end,
):
    """Return a FreeCAD vector from start to end."""

    return FreeCAD.Vector(
        end.x - start.x,
        end.y - start.y,
        end.z - start.z,
    )


def extended_for_dual_copes(physical_start, physical_end, profile, obj):
    direction=vector_between(physical_start,physical_end)
    length=direction.Length
    if length <= 0:
        raise ValueError("Cannot cope a zero-length member.")
    unit=FreeCAD.Vector(direction.x/length,direction.y/length,direction.z/length)
    start_extra=0.0; end_extra=0.0
    for p in ("StartCope","StartCope2","StartCope3"):
        if bool(getattr(obj,p+"Enabled",False)):
            start_extra=max(start_extra,temporary_cope_extension(
                physical_start,physical_end,profile,
                getattr(obj,p+"ThroughStart"),getattr(obj,p+"ThroughEnd"),
                float(getattr(obj,p+"ThroughDiameter"))))
    for p in ("EndCope","EndCope2","EndCope3"):
        if bool(getattr(obj,p+"Enabled",False)):
            end_extra=max(end_extra,temporary_cope_extension(
                physical_start,physical_end,profile,
                getattr(obj,p+"ThroughStart"),getattr(obj,p+"ThroughEnd"),
                float(getattr(obj,p+"ThroughDiameter"))))
    return (
        FreeCAD.Vector(physical_start.x-unit.x*start_extra,physical_start.y-unit.y*start_extra,physical_start.z-unit.z*start_extra),
        FreeCAD.Vector(physical_end.x+unit.x*end_extra,physical_end.y+unit.y*end_extra,physical_end.z+unit.z*end_extra),
    )




def apply_cope_to_existing_shape(
    shape,
    through_start,
    through_end,
    through_outside_diameter,
    keep_point,
):
    """Subtract one target cylinder from an existing tube shape."""

    diameter = validate_cope_diameter(
        through_outside_diameter
    )

    cutter = build_through_tube_cutting_tool(
        through_start,
        through_end,
        diameter,
    )

    cut_shape = shape.cut(
        cutter
    )

    return primary_cope_component(
        cut_shape,
        keep_point,
    )


def bounded_cope_target_axis(
    target_member,
    fallback_start,
    fallback_end,
):
    """Return the finite physical axis of a secondary cope target.

    Primary fishmouth cutters intentionally extend beyond the target axis so a
    complete saddle can form. A secondary branch-to-branch cope at a compound
    corner must not extend the target through the joint: doing so mirrors the
    inside relief onto the outside of the corner.
    """
    if (
        target_member is not None
        and hasattr(target_member, "StartPoint")
        and hasattr(target_member, "EndPoint")
    ):
        try:
            return physical_member_endpoints(target_member)
        except Exception:
            pass

    return (fallback_start, fallback_end)


def apply_bounded_cope_to_existing_shape(
    shape,
    through_start,
    through_end,
    through_outside_diameter,
    keep_point,
):
    """Subtract only the finite physical target cylinder from a tube shape."""
    diameter = validate_cope_diameter(
        through_outside_diameter
    )

    cutter = build_through_tube_cutting_tool(
        through_start,
        through_end,
        diameter,
        extension=0.0,
    )

    cut_shape = shape.cut(
        cutter
    )

    return primary_cope_component(
        cut_shape,
        keep_point,
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
        -> temporary cope stock
        -> start cope
        -> end cope
        -> start miter
        -> end miter

    A tube may therefore have up to two sequential cylindrical copes at each end.
    """

    ensure_notch_properties(
        obj
    )

    design_length = design_member_length(
        obj.StartPoint,
        obj.EndPoint,
    )

    physical_start, physical_end = physical_member_endpoints(
        obj
    )

    has_end_specific_cope = (
        bool(
            obj.StartCopeEnabled
        )
        or bool(
            obj.EndCopeEnabled
        )
        or bool(
            obj.StartCope2Enabled
        )
        or bool(
            obj.EndCope2Enabled
        )
        or bool(
            obj.StartCope3Enabled
        )
        or bool(
            obj.EndCope3Enabled
        )
    )

    if has_end_specific_cope:
        temporary_start, temporary_end = (
            extended_for_dual_copes(
                physical_start,
                physical_end,
                profile,
                obj,
            )
        )

        shape, _ = plain_shape_builder(
            temporary_start,
            temporary_end,
            profile,
        )

        if bool(
            obj.StartCopeEnabled
        ):
            shape = apply_cope_to_existing_shape(
                shape,
                obj.StartCopeThroughStart,
                obj.StartCopeThroughEnd,
                obj.StartCopeThroughDiameter,
                physical_end,
            )

        if bool(obj.StartCope2Enabled):
            secondary_start, secondary_end = bounded_cope_target_axis(
                getattr(obj, "StartCope2TargetMember", None),
                obj.StartCope2ThroughStart,
                obj.StartCope2ThroughEnd,
            )
            shape = apply_bounded_cope_to_existing_shape(
                shape,
                secondary_start,
                secondary_end,
                obj.StartCope2ThroughDiameter,
                physical_end,
            )
        if bool(obj.StartCope3Enabled):
            tertiary_start, tertiary_end = bounded_cope_target_axis(
                getattr(obj, "StartCope3TargetMember", None),
                obj.StartCope3ThroughStart,
                obj.StartCope3ThroughEnd,
            )
            shape = apply_bounded_cope_to_existing_shape(
                shape,
                tertiary_start,
                tertiary_end,
                obj.StartCope3ThroughDiameter,
                physical_end,
            )

        if bool(
            obj.EndCopeEnabled
        ):
            shape = apply_cope_to_existing_shape(
                shape,
                obj.EndCopeThroughStart,
                obj.EndCopeThroughEnd,
                obj.EndCopeThroughDiameter,
                physical_start,
            )

        if bool(obj.EndCope2Enabled):
            secondary_start, secondary_end = bounded_cope_target_axis(
                getattr(obj, "EndCope2TargetMember", None),
                obj.EndCope2ThroughStart,
                obj.EndCope2ThroughEnd,
            )
            shape = apply_bounded_cope_to_existing_shape(
                shape,
                secondary_start,
                secondary_end,
                obj.EndCope2ThroughDiameter,
                physical_start,
            )
        if bool(obj.EndCope3Enabled):
            tertiary_start, tertiary_end = bounded_cope_target_axis(
                getattr(obj, "EndCope3TargetMember", None),
                obj.EndCope3ThroughStart,
                obj.EndCope3ThroughEnd,
            )
            shape = apply_bounded_cope_to_existing_shape(
                shape,
                tertiary_start,
                tertiary_end,
                obj.EndCope3ThroughDiameter,
                physical_start,
            )

    else:
        shape, _ = plain_shape_builder(
            physical_start,
            physical_end,
            profile,
        )

        # Legacy single-cope path.
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

    cutter_size = miter_cutter_size(
        physical_start,
        physical_end,
        profile,
    )

    if bool(
        obj.StartMiterEnabled
    ):
        shape = miter_tube_shape(
            tube_shape=shape,
            plane_point=obj.StartMiterPlanePoint,
            plane_normal=obj.StartMiterPlaneNormal,
            keep_point=obj.StartMiterKeepPoint,
            cutter_size=cutter_size,
        )

    if bool(
        obj.EndMiterEnabled
    ):
        shape = miter_tube_shape(
            tube_shape=shape,
            plane_point=obj.EndMiterPlanePoint,
            plane_normal=obj.EndMiterPlaneNormal,
            keep_point=obj.EndMiterKeepPoint,
            cutter_size=cutter_size,
        )

    return (
        shape,
        design_length,
    )
