"""Persistent FreeCAD storage for ForgeCAD joint treatments."""

import json

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



def normalize_cope_pairs(
    cope_pairs,
):
    """Return unique valid member-to-member cope layout-ID pairs."""

    normalized = []

    for pair in cope_pairs:
        try:
            coped_layout_id, target_layout_id = pair
        except (TypeError, ValueError):
            continue

        coped_layout_id = str(coped_layout_id).strip()
        target_layout_id = str(target_layout_id).strip()

        if (
            not coped_layout_id
            or not target_layout_id
            or coped_layout_id == target_layout_id
        ):
            continue

        value = (
            coped_layout_id,
            target_layout_id,
        )

        if value not in normalized:
            normalized.append(value)

    return tuple(normalized)


def encode_cope_pairs(
    cope_pairs,
):
    """Serialize explicit cope pairs for persistent storage."""

    return json.dumps(
        [
            [coped_layout_id, target_layout_id]
            for (
                coped_layout_id,
                target_layout_id,
            ) in normalize_cope_pairs(cope_pairs)
        ],
        separators=(",", ":"),
    )


def decode_cope_pairs(
    value,
):
    """Deserialize explicit cope pairs, safely tolerating stale data."""

    if value is None:
        return ()

    text = str(value).strip()

    if not text:
        return ()

    try:
        raw_pairs = json.loads(text)
    except (TypeError, ValueError):
        return ()

    if not isinstance(raw_pairs, list):
        return ()

    return normalize_cope_pairs(raw_pairs)


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

    if not hasattr(
        obj,
        "ExplicitCopePairs",
    ):
        obj.addProperty(
            "App::PropertyString",
            "ExplicitCopePairs",
            PROPERTY_GROUP,
        )

    for property_name in (
        "NodeKey",
        "TreatmentMode",
        "ThroughLayoutIDs",
        "ExplicitCopePairs",
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


def existing_treatment_group(
    document,
):
    """
    Return the existing Joint Treatments group without creating it.

    Read operations must not modify the FreeCAD document.
    """

    if document is None:
        return None

    return document.getObject(
        "ForgeCADJointTreatments"
    )


def treatment_objects(
    document,
):
    """
    Return all persistent ForgeCAD joint-treatment records.

    This is intentionally read-only. If the project does not yet
    contain a Joint Treatments group, an empty tuple is returned.
    """

    group = existing_treatment_group(
        document
    )

    if group is None:
        return ()

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
    """
    Create one persistent joint-treatment record.

    This is a write operation, so it may initialize the
    ForgeCAD project tree when necessary.
    """

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

    This function never creates or modifies document objects.
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



def load_joint_cope_pairs(
    document,
    requested_node_key,
):
    """
    Return explicit member-to-member cope pairs stored for one joint.

    Older treatment objects naturally load as an empty tuple.
    """

    obj = find_joint_treatment(
        document,
        requested_node_key,
    )

    if (
        obj is None
        or not hasattr(
            obj,
            "ExplicitCopePairs",
        )
    ):
        return ()

    return decode_cope_pairs(
        obj.ExplicitCopePairs
    )


def save_joint_cope_pair(
    document,
    requested_node_key,
    coped_layout_id,
    target_layout_id,
):
    """Add one explicit cope without replacing the primary treatment."""

    requested_node_key = str(
        requested_node_key
    ).strip()

    if not requested_node_key:
        raise ValueError(
            "Explicit cope requires a node key."
        )

    normalized_pair = normalize_cope_pairs(
        [
            (
                coped_layout_id,
                target_layout_id,
            )
        ]
    )

    if len(
        normalized_pair
    ) != 1:
        raise ValueError(
            "Explicit cope requires two different "
            "non-empty member layout IDs."
        )

    obj = find_joint_treatment(
        document,
        requested_node_key,
    )

    if obj is None:
        obj = create_joint_treatment_object(
            document
        )

    ensure_treatment_properties(
        obj
    )

    obj.NodeKey = requested_node_key

    if not str(
        obj.TreatmentMode
    ).strip():
        obj.TreatmentMode = "auto"

    existing_pairs = (
        load_joint_cope_pairs(
            document,
            requested_node_key,
        )
    )

    obj.ExplicitCopePairs = (
        encode_cope_pairs(
            existing_pairs
            + normalized_pair
        )
    )

    obj.Label = (
        f"Joint Treatment "
        f"{requested_node_key}"
    )

    document.recompute()

    return obj


def remove_joint_cope_pair(
    document,
    requested_node_key,
    coped_layout_id,
    target_layout_id,
):
    """Remove one explicit cope while preserving the primary treatment."""

    obj = find_joint_treatment(
        document,
        requested_node_key,
    )

    if (
        obj is None
        or not hasattr(
            obj,
            "ExplicitCopePairs",
        )
    ):
        return False

    requested_pair = (
        str(
            coped_layout_id
        ).strip(),
        str(
            target_layout_id
        ).strip(),
    )

    existing_pairs = list(
        load_joint_cope_pairs(
            document,
            requested_node_key,
        )
    )

    if requested_pair not in existing_pairs:
        return False

    existing_pairs.remove(
        requested_pair
    )

    obj.ExplicitCopePairs = (
        encode_cope_pairs(
            existing_pairs
        )
    )

    document.recompute()

    return True


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

    group = existing_treatment_group(
        document
    )

    if group is not None:
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

def replace_joint_cope_pairs(document, requested_node_key, cope_pairs):
    """Atomically replace only the additive operations on one joint record.

    The caller owns the FreeCAD transaction and regeneration. Primary mode,
    miter identities, and other joint records are never changed here.
    """
    import json
    from forgecad.adapters.freecad.joint_pair_validation import normalized_pairs

    key = str(requested_node_key or "").strip()
    if not key:
        raise ValueError("A joint node key is required.")
    pairs = normalized_pairs(cope_pairs)
    obj = find_joint_treatment(document, key)
    if obj is not None:
        raw = str(getattr(obj, "ExplicitCopePairs", "") or "").strip()
        if raw:
            try:
                old = json.loads(raw)
                if not isinstance(old, list):
                    raise ValueError("Expected a list of cope pairs.")
                normalized_pairs(old)
            except (TypeError, ValueError) as error:
                raise ValueError("The stored cope list is malformed; refusing to overwrite it.") from error
    if obj is None:
        obj = create_joint_treatment_object(document)
    ensure_treatment_properties(obj)
    obj.NodeKey = key
    if not str(obj.TreatmentMode or "").strip():
        obj.TreatmentMode = "auto"
        obj.ThroughLayoutIDs = ""
    obj.ExplicitCopePairs = encode_cope_pairs(pairs)
    obj.Label = "Joint Treatment " + key
    document.recompute()
    return obj

def _ensure_explicit_through_pairs_property(obj):
    """Ensure one treatment object can persist selection-first Through pairs."""
    if not hasattr(obj, "ExplicitThroughPairs"):
        obj.addProperty(
            "App::PropertyString",
            "ExplicitThroughPairs",
            PROPERTY_GROUP,
        )
    try:
        obj.setEditorMode("ExplicitThroughPairs", 1)
    except Exception:
        pass


def load_joint_through_pairs(document, requested_node_key):
    """Return persisted branch->through pairs for one joint."""
    obj = find_joint_treatment(document, str(requested_node_key or "").strip())
    if obj is None or not hasattr(obj, "ExplicitThroughPairs"):
        return ()
    return decode_cope_pairs(obj.ExplicitThroughPairs)


def replace_joint_through_pairs(document, requested_node_key, through_pairs):
    """Replace only selection-first Through relationships for one joint.

    Primary treatment and ordinary ExplicitCopePairs are preserved.
    """
    import json
    from forgecad.adapters.freecad.joint_pair_validation import normalized_pairs

    key = str(requested_node_key or "").strip()
    if not key:
        raise ValueError("A joint node key is required.")
    pairs = normalized_pairs(through_pairs)
    obj = find_joint_treatment(document, key)
    if obj is not None and hasattr(obj, "ExplicitThroughPairs"):
        raw = str(getattr(obj, "ExplicitThroughPairs", "") or "").strip()
        if raw:
            try:
                old = json.loads(raw)
                if not isinstance(old, list):
                    raise ValueError("Expected a list of through pairs.")
                normalized_pairs(old)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "The stored through list is malformed; refusing to overwrite it."
                ) from error
    if obj is None:
        obj = create_joint_treatment_object(document)
    ensure_treatment_properties(obj)
    _ensure_explicit_through_pairs_property(obj)
    obj.NodeKey = key
    if not str(obj.TreatmentMode or "").strip():
        obj.TreatmentMode = "auto"
        obj.ThroughLayoutIDs = ""
    obj.ExplicitThroughPairs = encode_cope_pairs(pairs)
    obj.Label = "Joint Treatment " + key
    document.recompute()
    return obj
