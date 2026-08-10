"""FreeCAD document objects for ForgeCAD joint review status."""

import FreeCAD

from forgecad.adapters.freecad.document_tree import (
    clear_group,
    initialize_project_tree,
)
from forgecad.adapters.freecad.joint_status_adapter import (
    joint_review_for_document,
)


PROPERTY_GROUP = (
    "ForgeCAD Joint"
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

    for property_name in (
        "JointID",
        "NodeKey",
        "Position",
        "ReviewStatus",
        "Treatment",
        "Reviewed",
        "ManualTreatment",
        "NeedsAttention",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )

        except Exception:
            pass

    return obj


def create_joint_status_object(
    document,
    joint_id,
    item,
):
    """Create one FreeCAD joint-status object."""

    obj = document.addObject(
        "App::FeaturePython",
        "ForgeCADJoint",
    )

    ensure_joint_status_properties(
        obj
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

    obj.Label = (
        f"{joint_id} - "
        f"{item.status.label}"
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
