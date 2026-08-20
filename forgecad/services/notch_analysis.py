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
from forgecad.services.joint_treatment_resolver import (
    CopeInstruction,
    resolve_joint_treatment,
)


BRANCH_END_START = "start"
BRANCH_END_END = "end"


@dataclass(frozen=True, slots=True)
class NotchSpecification:
    """
    Describe one branch-tube cope against a traditional
    two-member through path.

    This remains for compatibility with the existing
    automatic notch renderer.
    """

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


@dataclass(frozen=True, slots=True)
class CopeSpecification:
    """
    Describe one generalized member-to-member cope.

    Unlike NotchSpecification, this does not require a
    two-member straight-through path.
    """

    joint: Joint

    coped_member: Member
    target_member: Member

    coped_end: str

    angle_degrees: float

    coped_outside_diameter: float
    coped_inside_diameter: float
    coped_wall_thickness: float

    target_outside_diameter: float


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

    The legacy automatic notch implementation requires both
    halves of the through path to use the same outside diameter.
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


def cope_angle(
    coped_member: Member,
    target_member: Member,
    joint_node: Node,
) -> float:
    """Return the acute fabrication angle for a member-to-member cope."""

    return branch_through_angle(
        coped_member,
        target_member,
        joint_node,
    )


def build_cope_specification(
    instruction: CopeInstruction,
) -> CopeSpecification:
    """Build one validated generalized cope specification."""

    joint = instruction.joint

    coped_member = (
        instruction.coped_member
    )

    target_member = (
        instruction.target_member
    )

    if (
        coped_member
        is target_member
    ):
        raise ValueError(
            "A member cannot be coped against itself."
        )

    if not member_touches_node(
        coped_member,
        joint.node,
    ):
        raise ValueError(
            "Coped member does not touch the joint."
        )

    if not member_touches_node(
        target_member,
        joint.node,
    ):
        raise ValueError(
            "Target member does not touch the joint."
        )

    angle = cope_angle(
        coped_member,
        target_member,
        joint.node,
    )

    if angle <= 1e-6:
        raise ValueError(
            "Cannot create a cope for collinear members."
        )

    coped_profile = (
        coped_member.profile
    )

    target_profile = (
        target_member.profile
    )

    return CopeSpecification(
        joint=joint,
        coped_member=coped_member,
        target_member=target_member,
        coped_end=member_end_at_node(
            coped_member,
            joint.node,
        ),
        angle_degrees=angle,
        coped_outside_diameter=float(
            coped_profile.outside_diameter
        ),
        coped_inside_diameter=float(
            coped_profile.inside_diameter
        ),
        coped_wall_thickness=float(
            coped_profile.wall_thickness
        ),
        target_outside_diameter=float(
            target_profile.outside_diameter
        ),
    )


def cope_specifications_for_treatment(
    treatment,
    straight_tolerance_degrees: float = 3.0,
) -> tuple[CopeSpecification, ...]:
    """
    Resolve a joint treatment and return all required cope specs.

    This is the generalized path used for corners, explicit
    designer treatments, and eventually all automatic joints.
    """

    resolution = resolve_joint_treatment(
        treatment,
        straight_tolerance_degrees=(
            straight_tolerance_degrees
        ),
    )

    return tuple(
        build_cope_specification(
            instruction
        )
        for instruction
        in resolution.cope_instructions
    )


def build_notch_specification(
    joint: Joint,
    branch_member: Member,
    through_members,
) -> NotchSpecification:
    """Build one validated legacy tube-notch specification."""

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
    Return legacy automatic notch specifications for a joint.

    This function intentionally remains unchanged in behavior
    until the FreeCAD renderer is migrated to CopeSpecification.
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
