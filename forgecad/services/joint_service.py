"""Joint detection services for ForgeCAD."""

from forgecad.fabrication import (
    BentMember,
    Frame,
    Joint,
    Node,
    StructuralMember,
)


POINT_TOLERANCE = 1e-6


def node_on_member(
    member: StructuralMember,
    node: Node,
    tolerance: float = POINT_TOLERANCE,
) -> bool:
    """Return True when a node lies on a structural member."""
    from forgecad.services.node_proximity import nodes_coincident

    if isinstance(member, BentMember):
        return (
            nodes_coincident(member.start, node, tolerance=tolerance)
            or nodes_coincident(member.end, node, tolerance=tolerance)
        )

    if (
        nodes_coincident(member.start, node, tolerance=tolerance)
        or nodes_coincident(member.end, node, tolerance=tolerance)
    ):
        return True

    ax, ay, az = float(member.start.x), float(member.start.y), float(member.start.z)
    bx, by, bz = float(member.end.x), float(member.end.y), float(member.end.z)
    px, py, pz = float(node.x), float(node.y), float(node.z)

    ab_x, ab_y, ab_z = bx - ax, by - ay, bz - az
    ap_x, ap_y, ap_z = px - ax, py - ay, pz - az

    length_squared = ab_x * ab_x + ab_y * ab_y + ab_z * ab_z
    if length_squared <= 1e-12:
        return False

    parameter = (
        ap_x * ab_x + ap_y * ab_y + ap_z * ab_z
    ) / length_squared

    if parameter < -tolerance or parameter > 1.0 + tolerance:
        return False

    parameter = max(0.0, min(1.0, parameter))
    nearest_x = ax + parameter * ab_x
    nearest_y = ay + parameter * ab_y
    nearest_z = az + parameter * ab_z

    dx, dy, dz = px - nearest_x, py - nearest_y, pz - nearest_z
    return dx * dx + dy * dy + dz * dz <= tolerance * tolerance



def member_touches_node(
    member: StructuralMember,
    node: Node,
) -> bool:
    """Return True when a structural member touches a node."""

    return node_on_member(
        member,
        node,
    )


def connected_members(
    frame: Frame,
    node: Node,
) -> list[StructuralMember]:
    """Return structural members connected to a node."""

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
    """Return unique structural connection nodes in first-seen order."""
    from forgecad.services.node_proximity import nodes_coincident

    nodes = []
    for member in frame.members:
        for node in (member.start, member.end):
            if any(
                nodes_coincident(node, existing, tolerance=POINT_TOLERANCE)
                for existing in nodes
            ):
                continue
            nodes.append(node)
    return nodes



def detect_joints(
    frame: Frame,
) -> list[Joint]:
    """
    Detect nodes where two or more frame members meet.

    A continuous straight member may pass through a joint without being
    physically split into two separate members.

    Bent members currently participate through their explicit start and
    end nodes only.
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
