"""Joint inspection services for ForgeCAD."""

from dataclasses import dataclass

from forgecad.fabrication import (
    Joint,
    Member,
)
from forgecad.services.joint_geometry import (
    analyze_joint,
)
from forgecad.services.joint_member_roles import (
    identify_member_roles,
)
from forgecad.services.notch_analysis import (
    notch_specifications_for_joint,
)


@dataclass(frozen=True, slots=True)
class JointMemberInspection:
    """Display-ready information about one joint member."""

    member: Member
    role: str
    length_mm: float
    outside_diameter_mm: float
    wall_thickness_mm: float


@dataclass(frozen=True, slots=True)
class JointAngleInspection:
    """Display-ready information about one member-pair angle."""

    first_member: Member
    second_member: Member
    angle_degrees: float


@dataclass(frozen=True, slots=True)
class JointNotchInspection:
    """Display-ready information about one required branch notch."""

    branch_member: Member
    branch_end: str
    angle_degrees: float
    branch_outside_diameter_mm: float
    through_outside_diameter_mm: float


@dataclass(frozen=True, slots=True)
class JointInspection:
    """Complete inspection information for one ForgeCAD joint."""

    joint: Joint
    classification: str
    member_count: int

    members: tuple[
        JointMemberInspection,
        ...,
    ]

    angles: tuple[
        JointAngleInspection,
        ...,
    ]

    notches: tuple[
        JointNotchInspection,
        ...,
    ]

    @property
    def node(self):
        """Return the inspected joint node."""

        return self.joint.node

    @property
    def through_member_count(self) -> int:
        """Return the number of identified through members."""

        return sum(
            1
            for member in self.members
            if member.role == "through"
        )

    @property
    def branch_member_count(self) -> int:
        """Return the number of identified branch members."""

        return sum(
            1
            for member in self.members
            if member.role == "branch"
        )

    @property
    def notch_count(self) -> int:
        """Return the number of required notches."""

        return len(
            self.notches
        )


def member_role(
    member: Member,
    through_members,
    branch_members,
) -> str:
    """Return the fabrication role of a member at a joint."""

    if member in through_members:
        return "through"

    if member in branch_members:
        return "branch"

    return "connected"


def inspect_joint(
    joint: Joint,
    straight_tolerance_degrees: float = 3.0,
) -> JointInspection:
    """Build complete display-ready information for a joint."""

    geometry = analyze_joint(
        joint,
        straight_tolerance_degrees=(
            straight_tolerance_degrees
        ),
    )

    roles = identify_member_roles(
        joint,
        straight_tolerance_degrees=(
            straight_tolerance_degrees
        ),
    )

    notch_specs = (
        notch_specifications_for_joint(
            joint,
            straight_tolerance_degrees=(
                straight_tolerance_degrees
            ),
        )
    )

    members = tuple(
        JointMemberInspection(
            member=member,
            role=member_role(
                member,
                roles.through_members,
                roles.branch_members,
            ),
            length_mm=float(
                member.length
            ),
            outside_diameter_mm=float(
                member.profile.outside_diameter
            ),
            wall_thickness_mm=float(
                member.profile.wall_thickness
            ),
        )
        for member in joint.members
    )

    angles = tuple(
        JointAngleInspection(
            first_member=angle.first_member,
            second_member=angle.second_member,
            angle_degrees=float(
                angle.angle_degrees
            ),
        )
        for angle in geometry.angles
    )

    notches = tuple(
        JointNotchInspection(
            branch_member=spec.branch_member,
            branch_end=spec.branch_end,
            angle_degrees=float(
                spec.angle_degrees
            ),
            branch_outside_diameter_mm=float(
                spec.branch_outside_diameter
            ),
            through_outside_diameter_mm=float(
                spec.through_outside_diameter
            ),
        )
        for spec in notch_specs
    )

    return JointInspection(
        joint=joint,
        classification=geometry.classification,
        member_count=joint.member_count,
        members=members,
        angles=angles,
        notches=notches,
    )
