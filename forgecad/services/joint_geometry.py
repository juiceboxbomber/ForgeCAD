"""Geometric analysis services for ForgeCAD joints."""

from dataclasses import dataclass
from math import acos, degrees, sqrt

from forgecad.fabrication import (
    BentMember,
    Joint,
    Node,
    StructuralMember,
)
from forgecad.geometry import Point3D
from forgecad.services.bent_tube_path import (
    build_bent_tube_centerline,
)


JOINT_STRAIGHT = "straight"
JOINT_CORNER = "corner"
JOINT_T = "t_joint"
JOINT_MULTI_MEMBER = "multi_member"
JOINT_INVALID = "invalid"

POINT_TOLERANCE = 1e-6


@dataclass(frozen=True, slots=True)
class JointAngle:
    """Angle between two structural members at a joint."""

    first_member: StructuralMember
    second_member: StructuralMember
    angle_degrees: float


@dataclass(frozen=True, slots=True)
class JointGeometryAnalysis:
    """Geometric description of one ForgeCAD joint."""

    joint: Joint
    classification: str
    angles: tuple[JointAngle, ...]


def _bent_member_centerline(
    member: BentMember,
):
    """Build the true 3D centerline for one bent structural member."""

    return build_bent_tube_centerline(
        member.tube,
        start_point=Point3D(
            member.start.x,
            member.start.y,
            member.start.z,
        ),
        initial_direction=member.initial_direction,
        initial_bend_normal=member.initial_bend_normal,
    )


def member_other_node(
    member: StructuralMember,
    joint_node: Node,
) -> Node:
    """Return the member endpoint opposite an endpoint joint node."""
    from forgecad.services.node_proximity import nodes_coincident

    if nodes_coincident(member.start, joint_node, tolerance=POINT_TOLERANCE):
        return member.end
    if nodes_coincident(member.end, joint_node, tolerance=POINT_TOLERANCE):
        return member.start
    raise ValueError("The joint node is not a member endpoint.")



def member_point_parameter(
    member: StructuralMember,
    node: Node,
    tolerance: float = POINT_TOLERANCE,
) -> float | None:
    """Return a finite-member parameter; bent members expose endpoints only."""
    from forgecad.services.node_proximity import nodes_coincident

    if isinstance(member, BentMember):
        if nodes_coincident(member.start, node, tolerance=tolerance):
            return 0.0
        if nodes_coincident(member.end, node, tolerance=tolerance):
            return 1.0
        return None

    ax, ay, az = float(member.start.x), float(member.start.y), float(member.start.z)
    bx, by, bz = float(member.end.x), float(member.end.y), float(member.end.z)
    px, py, pz = float(node.x), float(node.y), float(node.z)

    ab_x, ab_y, ab_z = bx - ax, by - ay, bz - az
    ap_x, ap_y, ap_z = px - ax, py - ay, pz - az
    length_squared = ab_x * ab_x + ab_y * ab_y + ab_z * ab_z
    if length_squared <= 1e-12:
        return None

    parameter = (ap_x * ab_x + ap_y * ab_y + ap_z * ab_z) / length_squared
    if parameter < -tolerance or parameter > 1.0 + tolerance:
        return None

    parameter = max(0.0, min(1.0, parameter))
    nearest_x = ax + parameter * ab_x
    nearest_y = ay + parameter * ab_y
    nearest_z = az + parameter * ab_z
    dx, dy, dz = px - nearest_x, py - nearest_y, pz - nearest_z
    if dx * dx + dy * dy + dz * dz > tolerance * tolerance:
        return None
    return parameter



def member_contains_node_interior(
    member: StructuralMember,
    node: Node,
    tolerance: float = POINT_TOLERANCE,
) -> bool:
    """Return True when a node lies inside a member, not at either end."""

    if isinstance(
        member,
        BentMember,
    ):
        # Interior curved-member joints need curve/node proximity logic.
        # For now bent members participate through endpoints only.
        return False

    parameter = (
        member_point_parameter(
            member,
            node,
            tolerance=tolerance,
        )
    )

    if parameter is None:
        return False

    return (
        parameter > tolerance
        and parameter < (
            1.0 - tolerance
        )
    )


def member_direction_from_node(
    member: StructuralMember,
    joint_node: Node,
) -> tuple[float, float, float]:
    """Return a unit direction from a joint into a structural member."""
    from forgecad.services.node_proximity import nodes_coincident

    if isinstance(member, BentMember):
        if nodes_coincident(member.start, joint_node, tolerance=POINT_TOLERANCE):
            direction = member.initial_direction.normalized()
            return (direction.x, direction.y, direction.z)

        if nodes_coincident(member.end, joint_node, tolerance=POINT_TOLERANCE):
            centerline = _bent_member_centerline(member)
            direction = centerline.end_direction.normalized()
            return (-direction.x, -direction.y, -direction.z)

        raise ValueError("The bent member does not touch the supplied joint node.")

    if nodes_coincident(member.start, joint_node, tolerance=POINT_TOLERANCE):
        other_node = member.end
        dx = other_node.x - joint_node.x
        dy = other_node.y - joint_node.y
        dz = other_node.z - joint_node.z
    elif nodes_coincident(member.end, joint_node, tolerance=POINT_TOLERANCE):
        other_node = member.start
        dx = other_node.x - joint_node.x
        dy = other_node.y - joint_node.y
        dz = other_node.z - joint_node.z
    else:
        parameter = member_point_parameter(member, joint_node)
        if parameter is None:
            raise ValueError("The member does not touch the supplied joint node.")
        dx = member.end.x - member.start.x
        dy = member.end.y - member.start.y
        dz = member.end.z - member.start.z

    magnitude = sqrt(dx * dx + dy * dy + dz * dz)
    if magnitude <= 0.0:
        raise ValueError("Cannot determine direction for a zero-length member.")
    return (dx / magnitude, dy / magnitude, dz / magnitude)



def angle_between_members(
    first_member: StructuralMember,
    second_member: StructuralMember,
    joint_node: Node,
) -> float:
    """
    Return the included angle between two structural members at a joint.

    The result is between 0 and 180 degrees.
    """

    first_direction = (
        member_direction_from_node(
            first_member,
            joint_node,
        )
    )

    second_direction = (
        member_direction_from_node(
            second_member,
            joint_node,
        )
    )

    dot_product = (
        first_direction[0]
        * second_direction[0]
        + first_direction[1]
        * second_direction[1]
        + first_direction[2]
        * second_direction[2]
    )

    # Protect acos from tiny floating-point excursions.
    dot_product = max(
        -1.0,
        min(
            1.0,
            dot_product,
        ),
    )

    return degrees(
        acos(
            dot_product
        )
    )


def joint_angles(
    joint: Joint,
) -> tuple[
    JointAngle,
    ...,
]:
    """Return every unique pairwise angle at a joint."""

    angles = []

    members = joint.members

    for first_index in range(
        len(
            members
        )
    ):
        for second_index in range(
            first_index + 1,
            len(
                members
            ),
        ):
            first_member = members[
                first_index
            ]

            second_member = members[
                second_index
            ]

            angle = (
                angle_between_members(
                    first_member,
                    second_member,
                    joint.node,
                )
            )

            angles.append(
                JointAngle(
                    first_member=first_member,
                    second_member=second_member,
                    angle_degrees=angle,
                )
            )

    return tuple(
        angles
    )


def is_straight_angle(
    angle_degrees: float,
    tolerance_degrees: float = 3.0,
) -> bool:
    """Return True when an angle is approximately 180 degrees."""

    return (
        abs(
            180.0
            - float(
                angle_degrees
            )
        )
        <= float(
            tolerance_degrees
        )
    )


def classify_joint(
    joint: Joint,
    straight_tolerance_degrees: float = 3.0,
) -> str:
    """Classify a joint from its member geometry."""

    member_count = joint.member_count

    if member_count < 2:
        return JOINT_INVALID

    # -------------------------------------------------
    # Continuous straight member with branch connection
    # -------------------------------------------------

    interior_members = [
        member
        for member in joint.members
        if member_contains_node_interior(
            member,
            joint.node,
        )
    ]

    if (
        member_count == 2
        and len(
            interior_members
        ) == 1
    ):
        return JOINT_T

    angles = joint_angles(
        joint
    )

    if member_count == 2:
        if is_straight_angle(
            angles[
                0
            ].angle_degrees,
            straight_tolerance_degrees,
        ):
            return JOINT_STRAIGHT

        return JOINT_CORNER

    if member_count == 3:
        has_straight_pair = any(
            is_straight_angle(
                angle.angle_degrees,
                straight_tolerance_degrees,
            )
            for angle in angles
        )

        if has_straight_pair:
            return JOINT_T

        return JOINT_MULTI_MEMBER

    return JOINT_MULTI_MEMBER


def analyze_joint(
    joint: Joint,
    straight_tolerance_degrees: float = 3.0,
) -> JointGeometryAnalysis:
    """Return complete geometric analysis for one joint."""

    return JointGeometryAnalysis(
        joint=joint,
        classification=(
            classify_joint(
                joint,
                straight_tolerance_degrees,
            )
        ),
        angles=joint_angles(
            joint
        ),
    )
