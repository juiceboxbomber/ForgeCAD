"""Resolve ForgeCAD joint treatments into fabrication cope instructions."""

from dataclasses import dataclass

from forgecad.fabrication import (
    Joint,
    Member,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
    JointTreatmentMode,
)
from forgecad.services.joint_member_roles import (
    identify_member_roles,
)


@dataclass(frozen=True, slots=True)
class CopeInstruction:
    """Describe one member-to-member cope operation."""

    joint: Joint
    coped_member: Member
    target_member: Member


@dataclass(frozen=True, slots=True)
class JointTreatmentResolution:
    """Resolved cylindrical cope instructions for one joint."""

    treatment: JointTreatment

    through_members: tuple[
        Member,
        ...,
    ]

    cope_instructions: tuple[
        CopeInstruction,
        ...,
    ]

    @property
    def cope_count(self) -> int:
        """Return the number of cylindrical cope operations."""

        return len(
            self.cope_instructions
        )


def resolve_automatic_treatment(
    treatment: JointTreatment,
    straight_tolerance_degrees: float = 3.0,
) -> JointTreatmentResolution:
    """Resolve ForgeCAD's automatic joint behavior."""

    joint = treatment.joint

    roles = identify_member_roles(
        joint,
        straight_tolerance_degrees=(
            straight_tolerance_degrees
        ),
    )

    if not roles.has_through_pair:
        return JointTreatmentResolution(
            treatment=treatment,
            through_members=(),
            cope_instructions=(),
        )

    target_member = (
        roles.through_members[
            0
        ]
    )

    instructions = tuple(
        CopeInstruction(
            joint=joint,
            coped_member=branch_member,
            target_member=target_member,
        )
        for branch_member
        in roles.branch_members
    )

    return JointTreatmentResolution(
        treatment=treatment,
        through_members=(
            roles.through_members
        ),
        cope_instructions=instructions,
    )


def resolve_member_through(
    treatment: JointTreatment,
) -> JointTreatmentResolution:
    """
    Resolve a single selected through member.

    Every branch is first coped against the selected through member.

    When exactly two branches share the joint, the second branch is
    then given a secondary cope against the first branch. This makes
    the branch-to-branch fit deterministic while keeping the selected
    through member untouched.

    If the two branch solids do not actually intersect, the secondary
    cylindrical subtraction is geometrically a no-op.
    """

    joint = treatment.joint

    through_member = (
        treatment.through_members[
            0
        ]
    )

    branch_members = tuple(
        member
        for member in joint.members
        if member is not through_member
    )

    instructions = [
        CopeInstruction(
            joint=joint,
            coped_member=member,
            target_member=through_member,
        )
        for member in branch_members
    ]

    if len(branch_members) == 2:
        first_branch = (
            branch_members[
                0
            ]
        )

        second_branch = (
            branch_members[
                1
            ]
        )

        instructions.append(
            CopeInstruction(
                joint=joint,
                coped_member=second_branch,
                target_member=first_branch,
            )
        )

    return JointTreatmentResolution(
        treatment=treatment,
        through_members=(
            through_member,
        ),
        cope_instructions=tuple(
            instructions
        ),
    )


def resolve_both_coped(
    treatment: JointTreatment,
) -> JointTreatmentResolution:
    """
    Resolve the legacy both-coped mode.

    The mode is now implemented as a shared planar miter,
    so it intentionally produces no cylindrical cope
    instructions.
    """

    return JointTreatmentResolution(
        treatment=treatment,
        through_members=(),
        cope_instructions=(),
    )


def resolve_through_pair(
    treatment: JointTreatment,
) -> JointTreatmentResolution:
    """Resolve an explicitly selected through pair."""

    joint = treatment.joint

    through_members = (
        treatment.through_members
    )

    target_member = (
        through_members[
            0
        ]
    )

    instructions = tuple(
        CopeInstruction(
            joint=joint,
            coped_member=member,
            target_member=target_member,
        )
        for member in joint.members
        if member not in through_members
    )

    return JointTreatmentResolution(
        treatment=treatment,
        through_members=through_members,
        cope_instructions=instructions,
    )


def resolve_joint_treatment(
    treatment: JointTreatment,
    straight_tolerance_degrees: float = 3.0,
) -> JointTreatmentResolution:
    """Resolve a joint treatment into cylindrical cope instructions."""

    if (
        treatment.mode
        == JointTreatmentMode.AUTO
    ):
        return resolve_automatic_treatment(
            treatment,
            straight_tolerance_degrees=(
                straight_tolerance_degrees
            ),
        )

    if (
        treatment.mode
        == JointTreatmentMode.MEMBER_THROUGH
    ):
        return resolve_member_through(
            treatment
        )

    if (
        treatment.mode
        == JointTreatmentMode.BOTH_COPED
    ):
        return resolve_both_coped(
            treatment
        )

    if (
        treatment.mode
        == JointTreatmentMode.THROUGH_PAIR
    ):
        return resolve_through_pair(
            treatment
        )

    raise ValueError(
        "Unsupported joint treatment mode."
    )
