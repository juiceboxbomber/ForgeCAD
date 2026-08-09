"""Mathematical notch analysis for ForgeCAD tube joints."""

from dataclasses import dataclass

from forgecad.fabrication import (
    Joint,
    Member,
    Node,
)
from forgecad.services.joint_geometry import (
    angle_between_members,
)
from forgecad.services.joint_service import (
    member_touches_node,
)
from forgecad.services.joint_member_roles import (
    identify_member_roles,
)


BRANCH_END_START = "start"
BRANCH_END_END = "end"


@dataclass(frozen=True, slots=True)
class NotchSpecification:
    """Describe one branch-tube cope against a through tube."""

    joint: Joint

    branch_member: Member

    through_members: tuple[
        Member,
        Member,
    ]

    branch_end: str

    angle_degrees: float

    branch_outside_diameter: float
    branch_inside_diameter: float
    branch_wall_thickness: float

    through_outside_diameter: float


def member_end_at_node(
    member: Member,
    node: Node,
) -> str:
    """Return which end of a member terminates at the node."""

    if member.start == node:
        return BRANCH_END_START

    if member.end == node:
        return BRANCH_END_END

    raise ValueError(
        "The member does not touch the supplied node."
    )


def through_outside_diameter(
    through_members,
    tolerance: float = 1e-6,
) -> float:
    """
    Return the common outside diameter of a through pair.

    The first notch implementation requires both halves of
    the through path to use the same outside diameter.
    """

    if len(
        through_members
    ) != 2:
        raise ValueError(
            "A notch requires exactly two through members."
        )

    first_diameter = float(
        through_members[
            0
        ].profile.outside_diameter
    )

    second_diameter = float(
        through_members[
            1
        ].profile.outside_diameter
    )

    if (
        abs(
            first_diameter
            - second_diameter
        )
        > float(tolerance)
    ):
        raise ValueError(
            "Through members must have the same "
            "outside diameter for notch analysis."
        )

    return first_diameter


def branch_through_angle(
    branch_member: Member,
    through_member: Member,
    joint_node: Node,
) -> float:
    """
    Return the acute fabrication angle between branch
    and through tube centerlines.
    """

    raw_angle = angle_between_members(
        branch_member,
        through_member,
        joint_node,
    )

    return min(
        raw_angle,
        180.0 - raw_angle,
    )


def build_notch_specification(
    joint: Joint,
    branch_member: Member,
    through_members,
) -> NotchSpecification:
    """Build one validated tube-notch specification."""

    if not member_touches_node(
        branch_member,
        joint.node,
    ):
        raise ValueError(
            "Branch member does not touch the joint."
        )

    through_members = tuple(
        through_members
    )

    if len(
        through_members
    ) != 2:
        raise ValueError(
            "A notch requires exactly two through members."
        )

    if branch_member in through_members:
        raise ValueError(
            "The branch member cannot also be a through member."
        )

    for member in through_members:
        if not member_touches_node(
            member,
            joint.node,
        ):
            raise ValueError(
                "Every through member must touch the joint."
            )

    target_diameter = (
        through_outside_diameter(
            through_members
        )
    )

    angle = branch_through_angle(
        branch_member,
        through_members[0],
        joint.node,
    )

    if angle <= 1e-6:
        raise ValueError(
            "Cannot create a notch for collinear members."
        )

    profile = (
        branch_member.profile
    )

    return NotchSpecification(
        joint=joint,
        branch_member=branch_member,
        through_members=(
            through_members[0],
            through_members[1],
        ),
        branch_end=member_end_at_node(
            branch_member,
            joint.node,
        ),
        angle_degrees=angle,
        branch_outside_diameter=float(
            profile.outside_diameter
        ),
        branch_inside_diameter=float(
            profile.inside_diameter
        ),
        branch_wall_thickness=float(
            profile.wall_thickness
        ),
        through_outside_diameter=(
            target_diameter
        ),
    )


def notch_specifications_for_joint(
    joint: Joint,
    straight_tolerance_degrees: float = 3.0,
) -> tuple[NotchSpecification, ...]:
    """
    Return notch specifications for all branches at a joint.

    Joints without a valid through pair return no notch specs.
    """

    roles = identify_member_roles(
        joint,
        straight_tolerance_degrees=(
            straight_tolerance_degrees
        ),
    )

    if not roles.has_through_pair:
        return ()

    if not roles.branch_members:
        return ()

    return tuple(
        build_notch_specification(
            joint,
            branch_member,
            roles.through_members,
        )
        for branch_member
        in roles.branch_members
    )
