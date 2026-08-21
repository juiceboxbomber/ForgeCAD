"""Persistent FreeCAD storage for ForgeCAD joint constraints."""

import FreeCAD

from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)
from forgecad.fabrication.joint_constraint import (
    CollinearThroughConstraint,
    JointConstraintKind,
)
from forgecad.geometry.point import Point3D


CONSTRAINT_OBJECT_NAME = (
    "ForgeCADJointConstraint"
)

CONSTRAINT_GROUP_NAME = (
    "ForgeCADJointConstraints"
)

PROPERTY_GROUP = (
    "ForgeCAD Joint Constraint"
)


def coordinate_key(
    x,
    y,
    z,
    precision=6,
):
    """Return the stable coordinate key used for persisted joint constraints."""

    return (
        f"{float(x):.{precision}f},"
        f"{float(y):.{precision}f},"
        f"{float(z):.{precision}f}"
    )


def vector_key(
    vector,
    precision=6,
):
    """Return the persistent node key for a FreeCAD-like vector."""

    return coordinate_key(
        vector.x,
        vector.y,
        vector.z,
        precision=precision,
    )


def ensure_constraint_properties(
    obj,
):
    """Ensure a FreeCAD object contains joint-constraint metadata."""

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
        "ConstraintKind",
    ):
        obj.addProperty(
            "App::PropertyString",
            "ConstraintKind",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "AxisStart",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "AxisStart",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "AxisEnd",
    ):
        obj.addProperty(
            "App::PropertyVector",
            "AxisEnd",
            PROPERTY_GROUP,
        )

    for property_name in (
        "NodeKey",
        "ConstraintKind",
        "AxisStart",
        "AxisEnd",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj


def is_joint_constraint_object(
    obj,
):
    """Return True for a ForgeCAD joint-constraint record."""

    return (
        hasattr(
            obj,
            "NodeKey",
        )
        and hasattr(
            obj,
            "ConstraintKind",
        )
        and hasattr(
            obj,
            "AxisStart",
        )
        and hasattr(
            obj,
            "AxisEnd",
        )
    )


def existing_constraint_group(
    document,
):
    """
    Return the existing Joint Constraints group without creating it.

    Read operations must not modify the FreeCAD document.
    """

    if document is None:
        return None

    return document.getObject(
        CONSTRAINT_GROUP_NAME
    )


def constraint_objects(
    document,
):
    """Return all persistent ForgeCAD joint-constraint records."""

    group = existing_constraint_group(
        document
    )

    if group is None:
        return ()

    return tuple(
        obj
        for obj in group.Group
        if is_joint_constraint_object(
            obj
        )
    )


def find_joint_constraint(
    document,
    requested_node_key,
):
    """Return the constraint stored for a node key, if any."""

    requested_node_key = str(
        requested_node_key
    ).strip()

    for obj in constraint_objects(
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


def create_joint_constraint_object(
    document,
):
    """Create one persistent joint-constraint record."""

    groups = initialize_project_tree(
        document
    )

    obj = document.addObject(
        "App::FeaturePython",
        CONSTRAINT_OBJECT_NAME,
    )

    obj.Label = (
        "Joint Constraint"
    )

    ensure_constraint_properties(
        obj
    )

    groups[
        "Joint Constraints"
    ].addObject(
        obj
    )

    return obj


def _constraint_kind_value(
    constraint,
):
    kind = getattr(
        constraint,
        "kind",
        None,
    )

    value = getattr(
        kind,
        "value",
        kind,
    )

    return str(
        value
    ).strip()


def _vector_from_point(
    point,
):
    return FreeCAD.Vector(
        float(
            point.x
        ),
        float(
            point.y
        ),
        float(
            point.z
        ),
    )


def save_joint_constraint(
    document,
    requested_node_key,
    constraint,
):
    """
    Create or update a persistent joint constraint for one node.
    """

    requested_node_key = str(
        requested_node_key
    ).strip()

    if not requested_node_key:
        raise ValueError(
            "Joint constraint requires a node key."
        )

    if not isinstance(
        constraint,
        CollinearThroughConstraint,
    ):
        raise ValueError(
            "Unsupported joint constraint type."
        )

    kind_value = (
        _constraint_kind_value(
            constraint
        )
    )

    if (
        kind_value
        != JointConstraintKind.COLLINEAR_THROUGH.value
    ):
        raise ValueError(
            "Unsupported joint constraint kind."
        )

    obj = find_joint_constraint(
        document,
        requested_node_key,
    )

    if obj is None:
        obj = create_joint_constraint_object(
            document
        )

    ensure_constraint_properties(
        obj
    )

    obj.NodeKey = (
        requested_node_key
    )

    obj.ConstraintKind = (
        kind_value
    )

    obj.AxisStart = _vector_from_point(
        constraint.axis_start
    )

    obj.AxisEnd = _vector_from_point(
        constraint.axis_end
    )

    obj.Label = (
        f"Joint Constraint "
        f"{requested_node_key}"
    )

    document.recompute()

    return obj


def load_joint_constraint(
    document,
    requested_node_key,
):
    """
    Return the stored first-class joint constraint for one node.

    None is returned when no persistent constraint exists or when the
    stored kind is unknown.
    """

    obj = find_joint_constraint(
        document,
        requested_node_key,
    )

    if obj is None:
        return None

    kind_value = str(
        obj.ConstraintKind
    ).strip()

    if (
        kind_value
        != JointConstraintKind.COLLINEAR_THROUGH.value
    ):
        return None

    start = obj.AxisStart
    end = obj.AxisEnd

    return CollinearThroughConstraint(
        axis_start=Point3D(
            float(
                start.x
            ),
            float(
                start.y
            ),
            float(
                start.z
            ),
        ),
        axis_end=Point3D(
            float(
                end.x
            ),
            float(
                end.y
            ),
            float(
                end.z
            ),
        ),
    )


def remove_joint_constraint(
    document,
    requested_node_key,
):
    """Remove a persistent constraint from one joint."""

    obj = find_joint_constraint(
        document,
        requested_node_key,
    )

    if obj is None:
        return False

    group = existing_constraint_group(
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
