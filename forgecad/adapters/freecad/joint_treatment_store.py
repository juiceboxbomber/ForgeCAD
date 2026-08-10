"""Persistent FreeCAD storage for ForgeCAD joint treatments."""

from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


TREATMENT_OBJECT_NAME = (
    "ForgeCADJointTreatment"
)

PROPERTY_GROUP = (
    "ForgeCAD Joint Treatment"
)


def coordinate_key(
    x,
    y,
    z,
    precision=6,
):
    """Return a stable serialized coordinate key."""

    return (
        f"{float(x):.{precision}f},"
        f"{float(y):.{precision}f},"
        f"{float(z):.{precision}f}"
    )


def node_key(
    node,
    precision=6,
):
    """Return a stable key for a ForgeCAD domain node."""

    return coordinate_key(
        node.x,
        node.y,
        node.z,
        precision=precision,
    )


def vector_key(
    vector,
    precision=6,
):
    """Return a stable key for a FreeCAD vector."""

    return coordinate_key(
        vector.x,
        vector.y,
        vector.z,
        precision=precision,
    )


def normalize_layout_ids(
    layout_ids,
):
    """Return unique non-empty layout IDs in stable order."""

    normalized = []

    for layout_id in layout_ids:
        value = str(
            layout_id
        ).strip()

        if not value:
            continue

        if value not in normalized:
            normalized.append(
                value
            )

    return tuple(
        normalized
    )


def encode_layout_ids(
    layout_ids,
):
    """Serialize layout IDs for persistent storage."""

    return "|".join(
        normalize_layout_ids(
            layout_ids
        )
    )


def decode_layout_ids(
    value,
):
    """Deserialize persistent layout IDs."""

    if value is None:
        return ()

    return normalize_layout_ids(
        str(value).split(
            "|"
        )
    )


def ensure_treatment_properties(
    obj,
):
    """Ensure a FreeCAD object contains joint-treatment metadata."""

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
        "TreatmentMode",
    ):
        obj.addProperty(
            "App::PropertyString",
            "TreatmentMode",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "ThroughLayoutIDs",
    ):
        obj.addProperty(
            "App::PropertyString",
            "ThroughLayoutIDs",
            PROPERTY_GROUP,
        )

    for property_name in (
        "NodeKey",
        "TreatmentMode",
        "ThroughLayoutIDs",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj


def is_joint_treatment_object(
    obj,
):
    """Return True for a ForgeCAD joint-treatment record."""

    return (
        hasattr(
            obj,
            "NodeKey",
        )
        and hasattr(
            obj,
            "TreatmentMode",
        )
        and hasattr(
            obj,
            "ThroughLayoutIDs",
        )
    )


def treatment_objects(
    document,
):
    """Return all persistent ForgeCAD joint-treatment records."""

    groups = initialize_project_tree(
        document
    )

    group = groups[
        "Joint Treatments"
    ]

    return tuple(
        obj
        for obj in group.Group
        if is_joint_treatment_object(
            obj
        )
    )


def find_joint_treatment(
    document,
    requested_node_key,
):
    """Return the treatment stored for a node key, if any."""

    requested_node_key = str(
        requested_node_key
    ).strip()

    for obj in treatment_objects(
        document
    ):
        if (
            str(
                obj.NodeKey
            ).strip()
            == requested_node_key
        ):
            return obj

    return None


def create_joint_treatment_object(
    document,
):
    """Create one persistent joint-treatment record."""

    groups = initialize_project_tree(
        document
    )

    obj = document.addObject(
        "App::FeaturePython",
        TREATMENT_OBJECT_NAME,
    )

    obj.Label = (
        "Joint Treatment"
    )

    ensure_treatment_properties(
        obj
    )

    groups[
        "Joint Treatments"
    ].addObject(
        obj
    )

    return obj


def save_joint_treatment(
    document,
    requested_node_key,
    mode,
    through_layout_ids=(),
):
    """
    Create or update a persistent joint-treatment record.

    One treatment record is stored per joint node.
    """

    requested_node_key = str(
        requested_node_key
    ).strip()

    if not requested_node_key:
        raise ValueError(
            "Joint treatment requires a node key."
        )

    mode_value = str(
        getattr(
            mode,
            "value",
            mode,
        )
    ).strip()

    if not mode_value:
        raise ValueError(
            "Joint treatment requires a mode."
        )

    layout_ids = (
        normalize_layout_ids(
            through_layout_ids
        )
    )

    obj = find_joint_treatment(
        document,
        requested_node_key,
    )

    if obj is None:
        obj = (
            create_joint_treatment_object(
                document
            )
        )

    ensure_treatment_properties(
        obj
    )

    obj.NodeKey = (
        requested_node_key
    )

    obj.TreatmentMode = (
        mode_value
    )

    obj.ThroughLayoutIDs = (
        encode_layout_ids(
            layout_ids
        )
    )

    obj.Label = (
        f"Joint Treatment "
        f"{requested_node_key}"
    )

    document.recompute()

    return obj


def load_joint_treatment(
    document,
    requested_node_key,
):
    """
    Return stored treatment data for a node.

    The result is a tuple containing:

        mode, through_layout_ids

    None is returned when the joint has no persistent treatment.
    """

    obj = find_joint_treatment(
        document,
        requested_node_key,
    )

    if obj is None:
        return None

    mode = str(
        obj.TreatmentMode
    ).strip()

    through_layout_ids = (
        decode_layout_ids(
            obj.ThroughLayoutIDs
        )
    )

    return (
        mode,
        through_layout_ids,
    )


def remove_joint_treatment(
    document,
    requested_node_key,
):
    """Remove a persistent treatment from one joint."""

    obj = find_joint_treatment(
        document,
        requested_node_key,
    )

    if obj is None:
        return False

    groups = initialize_project_tree(
        document
    )

    group = groups[
        "Joint Treatments"
    ]

    try:
        group.removeObject(
            obj
        )
    except Exception:
        pass

    document.removeObject(
        obj.Name
    )

    document.recompute()

    return True
