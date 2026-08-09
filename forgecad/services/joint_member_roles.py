"""Member-role analysis for ForgeCAD joints."""

from dataclasses import dataclass

from forgecad.fabrication import (
    Joint,
    Member,
)
from forgecad.services.joint_geometry import (
    angle_between_members,
    is_straight_angle,
)


@dataclass(frozen=True, slots=True)
class MemberRoleAnalysis:
    """Describe through and branch members at one joint."""

    joint: Joint
    through_members: tuple[Member, ...]
    branch_members: tuple[Member, ...]

    @property
    def has_through_pair(self) -> bool:
        """Return True when two through members were identified."""

        return (
            len(self.through_members)
            == 2
        )

    @property
    def branch_count(self) -> int:
        """Return the number of branch members."""

        return len(
            self.branch_members
        )


def straightest_member_pair(
    joint: Joint,
) -> tuple[Member, Member] | None:
    """
    Return the member pair with the largest included angle.

    None is returned when fewer than two members exist.
    """

    members = (
        joint.members
    )

    if len(members) < 2:
        return None

    best_pair = None
    best_angle = -1.0

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

            if angle > best_angle:
                best_angle = angle

                best_pair = (
                    first_member,
                    second_member,
                )

    return best_pair


def identify_member_roles(
    joint: Joint,
    straight_tolerance_degrees: float = 3.0,
) -> MemberRoleAnalysis:
    """
    Identify through and branch members at a joint.

    A through pair must be approximately straight.
    All remaining members are considered branches.
    """

    if joint.member_count < 2:
        return MemberRoleAnalysis(
            joint=joint,
            through_members=(),
            branch_members=tuple(
                joint.members
            ),
        )

    pair = straightest_member_pair(
        joint
    )

    if pair is None:
        return MemberRoleAnalysis(
            joint=joint,
            through_members=(),
            branch_members=tuple(
                joint.members
            ),
        )

    angle = angle_between_members(
        pair[0],
        pair[1],
        joint.node,
    )

    if not is_straight_angle(
        angle,
        tolerance_degrees=straight_tolerance_degrees,
    ):
        return MemberRoleAnalysis(
            joint=joint,
            through_members=(),
            branch_members=tuple(
                joint.members
            ),
        )

    branch_members = tuple(
        member
        for member in joint.members
        if member not in pair
    )

    return MemberRoleAnalysis(
        joint=joint,
        through_members=pair,
        branch_members=branch_members,
    )
