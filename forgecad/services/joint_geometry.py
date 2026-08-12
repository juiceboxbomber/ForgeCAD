"""Geometric analysis services for ForgeCAD joints."""

from dataclasses import dataclass
from math import acos, degrees, sqrt

from forgecad.fabrication import (
    Joint,
    Member,
    Node,
)


JOINT_STRAIGHT = "straight"
JOINT_CORNER = "corner"
JOINT_T = "t_joint"
JOINT_MULTI_MEMBER = "multi_member"
JOINT_INVALID = "invalid"

POINT_TOLERANCE = 1e-6


@dataclass(frozen=True, slots=True)
class JointAngle:
    """Angle between two members at a joint."""

    first_member: Member
    second_member: Member
    angle_degrees: float


@dataclass(frozen=True, slots=True)
class JointGeometryAnalysis:
    """Geometric description of one ForgeCAD joint."""

    joint: Joint
    classification: str
    angles: tuple[JointAngle, ...]


def member_other_node(
    member: Member,
    joint_node: Node,
) -> Node:
    """Return the member endpoint opposite an endpoint joint node."""

    if member.start == joint_node:
        return member.end

    if member.end == joint_node:
        return member.start

    raise ValueError(
        "The joint node is not a member endpoint."
    )


def member_point_parameter(
    member: Member,
    node: Node,
    tolerance: float = POINT_TOLERANCE,
) -> float | None:
    """
    Return the node position along a finite member.

    0.0 is the member start.
    1.0 is the member end.

    None is returned when the node is not on the member centerline.
    """

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
        return None

    parameter = (
        ap_x * ab_x
        + ap_y * ab_y
        + ap_z * ab_z
    ) / length_squared

    if (
        parameter < -tolerance
        or parameter > 1.0 + tolerance
    ):
        return None

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

    dx = px - nearest_x
    dy = py - nearest_y
    dz = pz - nearest_z

    distance_squared = (
        dx * dx
        + dy * dy
        + dz * dz
    )

    if (
        distance_squared
        > tolerance * tolerance
    ):
        return None

    return parameter


def member_contains_node_interior(
    member: Member,
    node: Node,
    tolerance: float = POINT_TOLERANCE,
) -> bool:
    """Return True when a node lies inside a member, not at either end."""

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
    member: Member,
    joint_node: Node,
) -> tuple[
    float,
    float,
    float,
]:
    """
    Return a unit vector along a member from a joint location.

    Endpoint joints point toward the opposite endpoint.

    When the joint lies inside a continuous member, a deterministic
    direction toward member.end is returned. The physical member
    remains one continuous member.
    """

    if member.start == joint_node:
        other_node = (
            member.end
        )

        dx = (
            other_node.x
            - joint_node.x
        )

        dy = (
            other_node.y
            - joint_node.y
        )

        dz = (
            other_node.z
            - joint_node.z
        )

    elif member.end == joint_node:
        other_node = (
            member.start
        )

        dx = (
            other_node.x
            - joint_node.x
        )

        dy = (
            other_node.y
            - joint_node.y
        )

        dz = (
            other_node.z
            - joint_node.z
        )

    else:
        parameter = (
            member_point_parameter(
                member,
                joint_node,
            )
        )

        if parameter is None:
            raise ValueError(
                "The member does not touch the supplied joint node."
            )

        dx = (
            member.end.x
            - member.start.x
        )

        dy = (
            member.end.y
            - member.start.y
        )

        dz = (
            member.end.z
            - member.start.z
        )

    magnitude = sqrt(
        dx * dx
        + dy * dy
        + dz * dz
    )

    if magnitude <= 0.0:
        raise ValueError(
            "Cannot determine direction for a zero-length member."
        )

    return (
        dx / magnitude,
        dy / magnitude,
        dz / magnitude,
    )


def angle_between_members(
    first_member: Member,
    second_member: Member,
    joint_node: Node,
) -> float:
    """
    Return the included angle between two members at a joint.

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

    members = (
        joint.members
    )

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
            first_member = (
                members[
                    first_index
                ]
            )

            second_member = (
                members[
                    second_index
                ]
            )

            angle = (
                angle_between_members(
                    first_member,
                    second_member,
                    joint.node,
                )
            )

            angles.append(
                JointAngle(
                    first_member=(
                        first_member
                    ),
                    second_member=(
                        second_member
                    ),
                    angle_degrees=(
                        angle
                    ),
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

    member_count = (
        joint.member_count
    )

    if member_count < 2:
        return JOINT_INVALID

    # -------------------------------------------------
    # Continuous member with branch connection
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
