"""Joint detection services for ForgeCAD."""

from forgecad.fabrication import (
    Frame,
    Joint,
    Member,
    Node,
)


POINT_TOLERANCE = 1e-6


def node_on_member(
    member: Member,
    node: Node,
    tolerance: float = POINT_TOLERANCE,
) -> bool:
    """Return True when a node lies on a member centerline segment."""

    if (
        member.start == node
        or member.end == node
    ):
        return True

    ax = float(
        member.start.x
    )
    ay = float(
        member.start.y
    )
    az = float(
        member.start.z
    )

    bx = float(
        member.end.x
    )
    by = float(
        member.end.y
    )
    bz = float(
        member.end.z
    )

    px = float(
        node.x
    )
    py = float(
        node.y
    )
    pz = float(
        node.z
    )

    ab_x = bx - ax
    ab_y = by - ay
    ab_z = bz - az

    ap_x = px - ax
    ap_y = py - ay
    ap_z = pz - az

    length_squared = (
        ab_x * ab_x
        + ab_y * ab_y
        + ab_z * ab_z
    )

    if length_squared <= 1e-12:
        return False

    parameter = (
        ap_x * ab_x
        + ap_y * ab_y
        + ap_z * ab_z
    ) / length_squared

    if (
        parameter < -tolerance
        or parameter > 1.0 + tolerance
    ):
        return False

    parameter = max(
        0.0,
        min(
            1.0,
            parameter,
        ),
)

    nearest_x = (
        ax
        + parameter * ab_x
    )

    nearest_y = (
        ay
        + parameter * ab_y
    )

    nearest_z = (
        az
        + parameter * ab_z
    )

    dx = (
        px - nearest_x
    )

    dy = (
        py - nearest_y
    )

    dz = (
        pz - nearest_z
    )

    distance_squared = (
        dx * dx
        + dy * dy
        + dz * dz
    )

    return (
        distance_squared
        <= tolerance * tolerance
    )


def member_touches_node(
    member: Member,
    node: Node,
) -> bool:
    """Return True when a member passes through a node."""

    return node_on_member(
        member,
        node,
    )


def connected_members(
    frame: Frame,
    node: Node,
) -> list[Member]:
    """Return frame members connected to a node."""

    return [
        member
        for member in frame.members
        if member_touches_node(
            member,
            node,
        )
    ]


def frame_connection_nodes(
    frame: Frame,
) -> list[Node]:
    """
    Return unique nodes referenced by frame members.

    Nodes are returned in first-seen member order.
    """

    nodes = []

    for member in frame.members:
        for node in (
            member.start,
            member.end,
        ):
            if node not in nodes:
                nodes.append(
                    node
                )

    return nodes


def detect_joints(
    frame: Frame,
) -> list[Joint]:
    """
    Detect nodes where two or more frame members meet.

    A continuous member may pass through a joint without being
    physically split into two separate members.
    """

    joints = []

    for node in frame_connection_nodes(
        frame
    ):
        members = connected_members(
            frame,
            node,
        )

        if len(
            members
        ) < 2:
            continue

        joint = Joint(
            node=node,
        )

        for member in members:
            joint.add_member(
                member
            )

        joints.append(
            joint
        )

    return joints
