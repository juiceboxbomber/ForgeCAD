"""FreeCAD document objects for ForgeCAD joint review status."""

import FreeCAD
import Part

from forgecad.adapters.freecad.document_tree import (
    clear_group,
    initialize_project_tree,
)
from forgecad.adapters.freecad.joint_status_adapter import (
    joint_review_for_document,
)
from forgecad.services.joint_status_visual import (
    joint_status_label,
    joint_status_visual,
)


PROPERTY_GROUP = (
    "ForgeCAD Joint"
)


MARKER_RADIUS_BY_CATEGORY = {
    "attention": 14.0,
    "manual": 11.0,
    "automatic": 9.0,
}


def marker_radius_for_category(
    category,
):
    """Return display-marker radius for a visual category."""

    return float(
        MARKER_RADIUS_BY_CATEGORY.get(
            str(
                category
            ).strip(),
            9.0,
        )
    )


def ensure_joint_status_properties(
    obj,
):
    """Ensure a FreeCAD object contains joint-status properties."""

    if not hasattr(
        obj,
        "JointID",
    ):
        obj.addProperty(
            "App::PropertyString",
            "JointID",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "NodeKey",
    ):
        obj.addProperty(
            "App::PropertyString",
            "NodeKey",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "Position",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "Position",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "ReviewStatus",
    ):
        obj.addProperty(
            "App::PropertyString",
            "ReviewStatus",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "Treatment",
    ):
        obj.addProperty(
            "App::PropertyString",
            "Treatment",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "Reviewed",
    ):
        obj.addProperty(
            "App::PropertyBool",
            "Reviewed",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "ManualTreatment",
    ):
        obj.addProperty(
            "App::PropertyBool",
            "ManualTreatment",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "NeedsAttention",
    ):
        obj.addProperty(
            "App::PropertyBool",
            "NeedsAttention",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "VisualStatus",
    ):
        obj.addProperty(
            "App::PropertyString",
            "VisualStatus",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "VisualSymbol",
    ):
        obj.addProperty(
            "App::PropertyString",
            "VisualSymbol",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "VisualCategory",
    ):
        obj.addProperty(
            "App::PropertyString",
            "VisualCategory",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "MarkerRadius",
    ):
        obj.addProperty(
            "App::PropertyLength",
            "MarkerRadius",
            PROPERTY_GROUP,
        )

    for property_name in (
        "JointID",
        "NodeKey",
        "Position",
        "ReviewStatus",
        "Treatment",
        "Reviewed",
        "ManualTreatment",
        "NeedsAttention",
        "VisualStatus",
        "VisualSymbol",
        "VisualCategory",
        "MarkerRadius",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )

        except Exception:
            pass

    return obj


def build_joint_marker_shape(
    position,
    radius,
):
    """Build a display-only sphere at a joint location."""

    radius = float(
        radius
    )

    if radius <= 0:
        raise ValueError(
            "Joint marker radius must be greater than zero."
        )

    center = FreeCAD.Vector(
        position.x,
        position.y,
        position.z,
    )

    return Part.makeSphere(
        radius,
        center,
    )


def configure_joint_marker(
    obj,
):
    """Apply display-only marker geometry to a joint-status object."""

    radius = marker_radius_for_category(
        obj.VisualCategory
    )

    obj.MarkerRadius = (
        radius
    )

    obj.Shape = build_joint_marker_shape(
        obj.Position,
        radius,
    )

    try:
        obj.ViewObject.Visibility = True
        obj.ViewObject.Transparency = 75
    except Exception:
        pass

    return obj


def create_joint_status_object(
    document,
    joint_id,
    item,
):
    """Create one FreeCAD joint-status object."""

    # Plain Part::Feature is intentional.
    #
    # Joint markers are disposable display/index objects and do
    # not require a Python proxy. Using Part::Feature ensures the
    # Shape is displayed by FreeCAD's normal Part view provider.
    obj = document.addObject(
        "Part::Feature",
        "ForgeCADJoint",
    )

    ensure_joint_status_properties(
        obj
    )

    visual = joint_status_visual(
        item.status
    )

    obj.JointID = (
        joint_id
    )

    obj.NodeKey = (
        item.node_key
    )

    obj.Position = FreeCAD.Vector(
        item.joint.node.x,
        item.joint.node.y,
        item.joint.node.z,
    )

    obj.ReviewStatus = (
        item.status.code.value
    )

    obj.Treatment = (
        item.status.label
    )

    obj.Reviewed = (
        item.status.is_reviewed
    )

    obj.ManualTreatment = (
        item.status.is_manual
    )

    obj.NeedsAttention = (
        item.status.needs_attention
    )

    obj.VisualStatus = (
        visual.code
    )

    obj.VisualSymbol = (
        visual.symbol
    )

    obj.VisualCategory = (
        visual.category
    )

    obj.Label = joint_status_label(
        joint_id,
        item.status,
    )

    configure_joint_marker(
        obj
    )

    return obj


def rebuild_joint_status_objects(
    document,
):
    """
    Rebuild the document's Joints group from current frame state.

    Existing status objects are disposable display/index objects.
    Persistent treatment data remains stored separately.
    """

    if document is None:
        return ()

    groups = initialize_project_tree(
        document
    )

    joints_group = groups[
        "Joints"
    ]

    clear_group(
        document,
        joints_group,
    )

    review = (
        joint_review_for_document(
            document
        )
    )

    created = []

    for index, item in enumerate(
        review.joints,
        start=1,
    ):
        joint_id = (
            f"J{index:03d}"
        )

        obj = create_joint_status_object(
            document,
            joint_id,
            item,
        )

        joints_group.addObject(
            obj
        )

        created.append(
            obj
        )

    document.recompute()

    return tuple(
        created
    )
