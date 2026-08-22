"""Safe cleanup helpers for unused ForgeCAD endpoint nodes."""


def object_references_node(
    obj,
    node_object,
):
    """
    Return True when a ForgeCAD object persistently references a node.

    Straight members and bent tubes both use StartNode/EndNode links.
    """

    if (
        obj is None
        or node_object is None
    ):
        return False

    for property_name in (
        "StartNode",
        "EndNode",
    ):
        if not hasattr(
            obj,
            property_name,
        ):
            continue

        try:
            linked_node = getattr(
                obj,
                property_name,
            )
        except Exception:
            continue

        if linked_node is node_object:
            return True

    return False


def node_is_referenced(
    document,
    node_object,
):
    """Return True when any remaining document object references the node."""

    if (
        document is None
        or node_object is None
    ):
        return False

    for obj in getattr(
        document,
        "Objects",
        (),
    ):
        if obj is node_object:
            continue

        if object_references_node(
            obj,
            node_object,
        ):
            return True

    return False


def remove_node_if_unused(
    document,
    node_object,
):
    """
    Remove one endpoint node only when no remaining object references it.

    The node is detached from its containing groups when possible before
    the document object itself is removed.
    """

    if (
        document is None
        or node_object is None
    ):
        return False

    if node_is_referenced(
        document,
        node_object,
    ):
        return False

    node_name = getattr(
        node_object,
        "Name",
        None,
    )

    if not node_name:
        return False

    for obj in tuple(
        getattr(
            document,
            "Objects",
            (),
        )
    ):
        group = getattr(
            obj,
            "Group",
            None,
        )

        if group is None:
            continue

        if node_object not in group:
            continue

        try:
            obj.removeObject(
                node_object
            )
        except Exception:
            pass

    try:
        document.removeObject(
            node_name
        )
    except Exception:
        return False

    return True
