"""Joint detection services for ForgeCAD."""

from forgecad.fabrication import (
    Frame,
    Joint,
    Member,
    Node,
)


def member_touches_node(
    member: Member,
    node: Node,
) -> bool:
    """Return True when a member starts or ends at a node."""

    return (
        member.start == node
        or member.end == node
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

    Free ends containing only one member are intentionally
    excluded from the returned joint list.
    """

    joints = []

    for node in frame_connection_nodes(
        frame
    ):
        members = connected_members(
            frame,
            node,
        )

        if len(members) < 2:
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
