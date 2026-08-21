"""Helpers for mirroring persistent ForgeCAD joint-treatment data."""

from forgecad.fabrication import (
    Node,
)
from forgecad.services.member_mirror import (
    mirror_node_across_centerline,
    mirror_node_across_plane,
)


def node_from_key(
    node_key,
) -> Node:
    """Return a domain Node from a serialized ForgeCAD node key."""

    parts = [
        part.strip()
        for part in str(
            node_key
        ).split(
            ","
        )
    ]

    if len(
        parts
    ) != 3:
        raise ValueError(
            "Invalid joint node key."
        )

    try:
        x, y, z = (
            float(
                part
            )
            for part in parts
        )

    except ValueError as error:
        raise ValueError(
            "Invalid joint node key."
        ) from error

    return Node(
        x,
        y,
        z,
    )


def node_key_from_node(
    node,
    precision=6,
):
    """Return the persistent coordinate key for a domain node."""

    return (
        f"{float(node.x):.{precision}f},"
        f"{float(node.y):.{precision}f},"
        f"{float(node.z):.{precision}f}"
    )


def mirror_node_key_across_centerline(
    source_node_key,
    center_start,
    center_end,
):
    """Return a joint node key reflected across an XY centerline."""

    source_node = node_from_key(
        source_node_key
    )

    mirrored = (
        mirror_node_across_centerline(
            source_node,
            center_start,
            center_end,
        )
    )

    return node_key_from_node(
        mirrored
    )


def mirror_node_key_across_plane(
    source_node_key,
    plane,
):
    """Return a joint node key reflected across a principal plane."""

    source_node = node_from_key(
        source_node_key
    )

    mirrored = (
        mirror_node_across_plane(
            source_node,
            plane,
        )
    )

    return node_key_from_node(
        mirrored
    )


def remap_through_layout_ids(
    source_layout_ids,
    layout_id_map,
):
    """
    Remap through-member layout IDs to their mirrored counterparts.

    None is returned when any required source layout was not mirrored.
    That prevents a mirrored treatment from referencing geometry on the
    original side of the chassis.
    """

    mirrored_ids = []

    for source_layout_id in source_layout_ids:
        source_layout_id = str(
            source_layout_id
        ).strip()

        if not source_layout_id:
            continue

        mirrored_layout_id = (
            layout_id_map.get(
                source_layout_id
            )
        )

        if not mirrored_layout_id:
            return None

        if (
            mirrored_layout_id
            not in mirrored_ids
        ):
            mirrored_ids.append(
                mirrored_layout_id
            )

    return tuple(
        mirrored_ids
    )


def mirrored_treatment_data(
    mode,
    through_layout_ids,
    layout_id_map,
):
    """
    Return treatment data suitable for the mirrored joint.

    Treatments without through-member references, such as a both-mitered
    joint, can be copied directly.

    Treatments that reference through members are copied only when every
    referenced source layout ID has a mirrored replacement.
    """

    mode_value = str(
        getattr(
            mode,
            "value",
            mode,
        )
    ).strip()

    if not mode_value:
        return None

    mirrored_layout_ids = (
        remap_through_layout_ids(
            through_layout_ids,
            layout_id_map,
        )
    )

    if mirrored_layout_ids is None:
        return None

    return (
        mode_value,
        mirrored_layout_ids,
    )
