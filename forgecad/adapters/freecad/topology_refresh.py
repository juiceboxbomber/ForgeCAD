"""Shared post-topology refresh for ForgeCAD FreeCAD documents."""


def synchronize_joint_constraints(
    document,
):
    """
    Synchronize persistent joint constraints from current joint topology.

    Eligible split straight-through joints receive a persisted
    CollinearThroughConstraint. Constraint records whose node keys are no
    longer present as constrained joints are removed.
    """

    if document is None:
        return ()

    from forgecad.adapters.freecad.joint_constraint_store import (
        constraint_objects,
        remove_joint_constraint,
        save_joint_constraint,
    )
    from forgecad.adapters.freecad.joint_status_adapter import (
        joint_review_for_document,
    )
    from forgecad.services.joint_constraints import (
        collinear_through_constraint_for_joint,
    )

    review = joint_review_for_document(
        document
    )

    active_node_keys = set()
    synchronized = []

    for item in review.joints:
        constraint = (
            collinear_through_constraint_for_joint(
                item.joint
            )
        )

        if constraint is None:
            continue

        node_key = str(
            item.node_key
        ).strip()

        if not node_key:
            continue

        active_node_keys.add(
            node_key
        )

        obj = save_joint_constraint(
            document,
            node_key,
            constraint,
        )

        synchronized.append(
            obj
        )

    stale_node_keys = [
        str(
            obj.NodeKey
        ).strip()
        for obj in constraint_objects(
            document
        )
        if (
            str(
                obj.NodeKey
            ).strip()
            not in active_node_keys
        )
    ]

    for node_key in stale_node_keys:
        remove_joint_constraint(
            document,
            node_key,
        )

    return tuple(
        synchronized
    )


def refresh_joint_topology(
    document,
):
    """
    Refresh derived joint state after structural geometry changes.

    Joint-status marker objects are disposable derived objects. Persistent
    joint constraints are synchronized from the same current topology so
    editing and fabrication analysis share one definition of each joint.
    """

    if document is None:
        return (
            (),
            (),
        )

    from forgecad.adapters.freecad.joint_status_objects import (
        rebuild_joint_status_objects,
    )

    markers = rebuild_joint_status_objects(
        document
    )

    constraints = synchronize_joint_constraints(
        document
    )

    return (
        markers,
        constraints,
    )
