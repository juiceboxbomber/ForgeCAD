"""FreeCAD adapter for trimming/extending ForgeCAD structural members."""
from forgecad.fabrication import BentMember

from forgecad.adapters.freecad.commands.create_member_between_nodes import (
    create_member_between_nodes,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    structural_member_from_freecad_object,
)
from forgecad.adapters.freecad.member_removal import (
    remove_member_and_unused_layout,
)
from forgecad.adapters.freecad.node_cleanup import (
    remove_node_if_unused,
)
from forgecad.adapters.freecad.topology_refresh import (
    refresh_joint_topology,
)
from forgecad.adapters.freecad.fabrication_refresh import (
    refresh_fabrication_for_document,
)
from forgecad.services.member_trim_extend import (
    bent_endpoint_intersection_3d,
    line_intersection_3d,
    modification_kind,
    replace_member_endpoint,
)


def _get_or_create_node(
    document,
    point,
):
    """
    Reuse ForgeCAD's normal node creation logic.

    Imported lazily so ordinary Python tests do not have to import the
    interactive FreeCAD command module during adapter collection.
    """

    from forgecad.adapters.freecad.commands.draw_member_interactive import (
        get_or_create_node,
    )

    return get_or_create_node(
        document,
        point,
    )


def endpoint_for_operation(
    parameter,
    endpoint=None,
):
    """
    Resolve which endpoint of the editable member should move.

    Extensions are unambiguous:
      parameter < 0 -> start
      parameter > 1 -> end

    Interior intersections are trims and require the caller to choose
    start or end explicitly. This keeps the geometry layer from guessing
    which side of the member the user intended to keep.
    """

    kind = modification_kind(
        parameter
    )

    if kind == "none":
        raise ValueError(
            "The target already intersects the member at its endpoint."
        )

    if kind == "extend":
        if parameter < 0.0:
            return "start"

        return "end"

    requested = str(
        endpoint or ""
    ).strip().lower()

    if requested not in (
        "start",
        "end",
    ):
        raise ValueError(
            "Trimming requires choosing the start or end side."
        )

    return requested


def old_endpoint_node(
    member_object,
    endpoint,
):
    """Return the source node that will cease to be this member's endpoint."""

    property_name = (
        "StartNode"
        if endpoint == "start"
        else "EndNode"
    )

    if not hasattr(
        member_object,
        property_name,
    ):
        return None

    try:
        return getattr(
            member_object,
            property_name,
        )
    except Exception:
        return None


def _is_joint_derived_bent_object(
    obj,
):
    """Return True when linked design nodes define the bent tube path."""

    proxy = getattr(
        obj,
        "Proxy",
        None,
    )

    if proxy is None:
        return False

    for method_name in (
        "_is_multi_joint_derived_bend",
        "_is_joint_derived_bend",
    ):
        method = getattr(
            proxy,
            method_name,
            None,
        )

        if not callable(
            method
        ):
            continue

        try:
            if method(
                obj
            ):
                return True
        except Exception:
            continue

    return False


def _trim_extend_bent_member_object(
    document,
    member_object,
    target_object,
    source_member,
    target_member,
    endpoint,
):
    """
    Move one true endpoint of a converted bend to a straight target.

    The bent FreeCAD object is retained. Its linked endpoint node is replaced
    and the existing joint-derived path machinery rebuilds the tube in place.
    """

    requested = str(
        endpoint or ""
    ).strip().lower()

    if requested not in (
        "start",
        "end",
    ):
        raise ValueError(
            "For a bent member, click the end you want to trim or extend."
        )

    if not _is_joint_derived_bent_object(
        member_object
    ):
        raise ValueError(
            "Bent Trim/Extend currently supports converted "
            "joint-derived bent tubes."
        )

    if isinstance(
        target_member,
        BentMember,
    ):
        raise ValueError(
            "Bent-member Trim/Extend currently requires a straight target."
        )

    (
        intersection,
        source_parameter,
        target_parameter,
        kind,
    ) = bent_endpoint_intersection_3d(
        source_member,
        target_member,
        requested,
    )

    if kind == "none":
        raise ValueError(
            "The target already intersects the bent member at that endpoint."
        )

    displaced_node = old_endpoint_node(
        member_object,
        requested,
    )

    replacement_node = _get_or_create_node(
        document,
        intersection,
    )

    property_name = (
        "StartNode"
        if requested == "start"
        else "EndNode"
    )

    setattr(
        member_object,
        property_name,
        replacement_node,
    )

    proxy = getattr(
        member_object,
        "Proxy",
        None,
    )

    if (
        proxy is not None
        and hasattr(
            proxy,
            "mark_geometry_dirty",
        )
    ):
        proxy.mark_geometry_dirty()

    document.recompute()

    remove_node_if_unused(
        document,
        displaced_node,
    )

    refresh_joint_topology(
        document
    )

    refresh_fabrication_for_document(
        document
    )

    return (
        None,
        member_object,
        intersection,
        requested,
        kind,
        source_parameter,
        target_parameter,
    )

def trim_extend_member_object(
    document,
    member_object,
    target_object,
    endpoint=None,
):
    """
    Trim or extend one ForgeCAD structural member to a target centerline.

    Straight sources retain the original replacement workflow.

    A converted bent source is updated in place. The caller must provide
    which physical end was clicked, and Phase 1 requires a straight target.
    """

    if document is None:
        raise ValueError(
            "Trim/Extend requires an active document."
        )

    if member_object is target_object:
        raise ValueError(
            "Trim/Extend requires two different members."
        )

    source_member = (
        structural_member_from_freecad_object(
            member_object
        )
    )

    target_member = (
        structural_member_from_freecad_object(
            target_object
        )
    )

    if isinstance(
        source_member,
        BentMember,
    ):
        return _trim_extend_bent_member_object(
            document,
            member_object,
            target_object,
            source_member,
            target_member,
            endpoint,
        )

    if isinstance(
        target_member,
        BentMember,
    ):
        raise ValueError(
            "Trim/Extend currently requires a straight target member."
        )

    (
        intersection,
        source_parameter,
        target_parameter,
    ) = line_intersection_3d(
        source_member,
        target_member,
    )

    resolved_endpoint = (
        endpoint_for_operation(
            source_parameter,
            endpoint=endpoint,
        )
    )

    displaced_node = (
        old_endpoint_node(
            member_object,
            resolved_endpoint,
        )
    )

    replacement_member = (
        replace_member_endpoint(
            source_member,
            intersection,
            resolved_endpoint,
        )
    )

    start_node_object = (
        _get_or_create_node(
            document,
            replacement_member.start,
        )
    )

    end_node_object = (
        _get_or_create_node(
            document,
            replacement_member.end,
        )
    )

    (
        replacement_layout_object,
        replacement_member_object,
    ) = create_member_between_nodes(
        document,
        start_node_object,
        end_node_object,
        profile=source_member.profile,
        material=source_member.material,
        refresh=False,
    )

    removed = (
        remove_member_and_unused_layout(
            document,
            member_object,
        )
    )

    if not removed:
        raise RuntimeError(
            "Trim/Extend created the replacement but could not remove "
            "the original member."
        )

    remove_node_if_unused(
        document,
        displaced_node,
    )

    document.recompute()

    refresh_joint_topology(
        document
    )

    refresh_fabrication_for_document(
        document
    )

    return (
        replacement_layout_object,
        replacement_member_object,
        intersection,
        resolved_endpoint,
        modification_kind(
            source_parameter
        ),
        source_parameter,
        target_parameter,
    )
