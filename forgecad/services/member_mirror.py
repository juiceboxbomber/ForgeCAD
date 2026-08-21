"""Geometry helpers for mirroring ForgeCAD frame members."""

import math

from forgecad.fabrication import (
    Member,
    Node,
)


DEFAULT_CENTERLINE_TOLERANCE = 1e-6


def mirror_node_across_y_zero(
    node: Node,
) -> Node:
    """
    Mirror a node across the legacy chassis plane Y=0.

    Kept for compatibility with the first mirror implementation.
    """

    return Node(
        node.x,
        -node.y,
        node.z,
    )


def node_is_on_y_zero(
    node: Node,
    tolerance=DEFAULT_CENTERLINE_TOLERANCE,
) -> bool:
    """Return True when a node lies on Y=0."""

    return (
        abs(
            float(
                node.y
            )
        )
        <= float(
            tolerance
        )
    )


def member_is_on_y_zero(
    member: Member,
    tolerance=DEFAULT_CENTERLINE_TOLERANCE,
) -> bool:
    """Return True when the entire member lies on Y=0."""

    return (
        node_is_on_y_zero(
            member.start,
            tolerance=tolerance,
        )
        and node_is_on_y_zero(
            member.end,
            tolerance=tolerance,
        )
    )


def mirror_member_across_y_zero(
    member: Member,
) -> Member:
    """Return a mirrored copy of a member across Y=0."""

    return Member(
        start=mirror_node_across_y_zero(
            member.start
        ),
        end=mirror_node_across_y_zero(
            member.end
        ),
        profile=member.profile,
        material=member.material,
    )


def mirror_members_across_y_zero(
    members,
):
    """Mirror members across Y=0, skipping centerline members."""

    mirrored = []

    for member in members:
        if member_is_on_y_zero(
            member
        ):
            continue

        mirrored.append(
            mirror_member_across_y_zero(
                member
            )
        )

    return tuple(
        mirrored
    )


def mirror_node_across_centerline(
    node: Node,
    center_start: Node,
    center_end: Node,
) -> Node:
    """
    Reflect a node across an arbitrary centerline in the XY plane.

    The centerline is treated as infinite. Z is preserved because this
    operation represents left/right chassis symmetry in plan view.
    """

    ax = float(
        center_start.x
    )
    ay = float(
        center_start.y
    )

    bx = float(
        center_end.x
    )
    by = float(
        center_end.y
    )

    px = float(
        node.x
    )
    py = float(
        node.y
    )

    dx = bx - ax
    dy = by - ay

    length_squared = (
        dx * dx
        + dy * dy
    )

    if length_squared <= (
        DEFAULT_CENTERLINE_TOLERANCE
        * DEFAULT_CENTERLINE_TOLERANCE
    ):
        raise ValueError(
            "Mirror centerline must have non-zero length."
        )

    projection_fraction = (
        (
            (px - ax) * dx
            + (py - ay) * dy
        )
        / length_squared
    )

    projected_x = (
        ax
        + projection_fraction * dx
    )

    projected_y = (
        ay
        + projection_fraction * dy
    )

    mirrored_x = (
        2.0 * projected_x
        - px
    )

    mirrored_y = (
        2.0 * projected_y
        - py
    )

    if math.isclose(
        mirrored_x,
        0.0,
        abs_tol=DEFAULT_CENTERLINE_TOLERANCE,
    ):
        mirrored_x = 0.0

    if math.isclose(
        mirrored_y,
        0.0,
        abs_tol=DEFAULT_CENTERLINE_TOLERANCE,
    ):
        mirrored_y = 0.0

    return Node(
        mirrored_x,
        mirrored_y,
        node.z,
    )


def mirror_member_across_centerline(
    member: Member,
    center_start: Node,
    center_end: Node,
) -> Member:
    """
    Reflect a member across an arbitrary XY chassis centerline.

    Tube profile and material are preserved.
    """

    return Member(
        start=mirror_node_across_centerline(
            member.start,
            center_start,
            center_end,
        ),
        end=mirror_node_across_centerline(
            member.end,
            center_start,
            center_end,
        ),
        profile=member.profile,
        material=member.material,
    )

def mirror_node_across_plane(
    node: Node,
    plane,
) -> Node:
    """
    Reflect a node across a principal plane through the origin.

    XY reverses Z.
    XZ reverses Y.
    YZ reverses X.
    """

    plane_name = str(
        plane
    ).strip().upper()

    if plane_name == "XY":
        return Node(
            node.x,
            node.y,
            -node.z,
        )

    if plane_name == "XZ":
        return Node(
            node.x,
            -node.y,
            node.z,
        )

    if plane_name == "YZ":
        return Node(
            -node.x,
            node.y,
            node.z,
        )

    raise ValueError(
        "Mirror plane must be XY, XZ, or YZ."
    )


def mirror_member_across_plane(
    member: Member,
    plane,
) -> Member:
    """
    Reflect a member across a principal plane through the origin.

    Tube profile and material are preserved.
    """

    return Member(
        start=mirror_node_across_plane(
            member.start,
            plane,
        ),
        end=mirror_node_across_plane(
            member.end,
            plane,
        ),
        profile=member.profile,
        material=member.material,
    )
