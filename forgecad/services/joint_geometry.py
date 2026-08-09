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
    """Return the member endpoint opposite the joint node."""

    if member.start == joint_node:
        return member.end

    if member.end == joint_node:
        return member.start

    raise ValueError(
        "The member does not touch the supplied joint node."
    )


def member_direction_from_node(
    member: Member,
    joint_node: Node,
) -> tuple[float, float, float]:
    """
    Return a unit vector pointing away from a joint
    along the member centerline.
    """

    other_node = member_other_node(
        member,
        joint_node,
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
) -> tuple[JointAngle, ...]:
    """Return every unique pairwise angle at a joint."""

    angles = []

    members = (
        joint.members
    )

    for first_index in range(
        len(members)
    ):
        for second_index in range(
            first_index + 1,
            len(members),
        ):
            first_member = (
                members[first_index]
            )

            second_member = (
                members[second_index]
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
            - float(angle_degrees)
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

    angles = joint_angles(
        joint
    )

    if member_count == 2:
        if is_straight_angle(
            angles[0].angle_degrees,
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
        classification=classify_joint(
            joint,
            straight_tolerance_degrees,
        ),
        angles=joint_angles(
            joint
        ),
    )
