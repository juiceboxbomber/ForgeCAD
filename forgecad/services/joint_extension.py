"""Fabrication extension analysis for ForgeCAD tube joints."""

from dataclasses import dataclass
from math import radians, sin

from forgecad.fabrication import (
    Joint,
    Member,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
    JointTreatmentMode,
)
from forgecad.services.joint_geometry import (
    angle_between_members,
)


MEMBER_END_START = "start"
MEMBER_END_END = "end"


@dataclass(frozen=True, slots=True)
class MemberExtensionSpecification:
    """Describe extra physical tube stock beyond one design node."""

    joint: Joint
    member: Member
    member_end: str
    extension_mm: float


def member_end_at_joint(
    member: Member,
    joint: Joint,
) -> str:
    """Return which member end lies at the joint."""

    if member.start == joint.node:
        return MEMBER_END_START

    if member.end == joint.node:
        return MEMBER_END_END

    raise ValueError(
        "Member does not touch the supplied joint."
    )


def fabrication_angle(
    first_member: Member,
    second_member: Member,
    joint: Joint,
) -> float:
    """Return the acute centerline angle between two members."""

    raw_angle = angle_between_members(
        first_member,
        second_member,
        joint.node,
    )

    return min(
        raw_angle,
        180.0 - raw_angle,
    )


def extension_to_outer_surface(
    extended_member: Member,
    intersecting_member: Member,
    joint: Joint,
) -> float:
    """
    Return required extension beyond the joint centerline.

    The extension reaches the outermost surface of the
    intersecting tube.

        extension = intersecting radius / sin(angle)
    """

    angle_degrees = fabrication_angle(
        extended_member,
        intersecting_member,
        joint,
    )

    angle_radians = radians(
        angle_degrees
    )

    sine = sin(
        angle_radians
    )

    if abs(
        sine
    ) <= 1e-9:
        raise ValueError(
            "Cannot calculate fabrication extension "
            "for collinear members."
        )

    target_radius = (
        float(
            intersecting_member.profile.outside_diameter
        )
        / 2.0
    )

    return (
        target_radius
        / abs(sine)
    )


def member_through_extensions(
    treatment: JointTreatment,
) -> tuple[
    MemberExtensionSpecification,
    ...,
]:
    """Return extension required for one through member."""

    through_member = (
        treatment.through_members[
            0
        ]
    )

    other_members = [
        member
        for member in treatment.joint.members
        if member is not through_member
    ]

    if not other_members:
        return ()

    required_extensions = [
        extension_to_outer_surface(
            through_member,
            other_member,
            treatment.joint,
        )
        for other_member in other_members
    ]

    # If several branches meet the same through member,
    # enough physical stock must exist for the largest
    # required outer-surface reach.
    extension = max(
        required_extensions
    )

    return (
        MemberExtensionSpecification(
            joint=treatment.joint,
            member=through_member,
            member_end=member_end_at_joint(
                through_member,
                treatment.joint,
            ),
            extension_mm=extension,
        ),
    )


def both_coped_extensions(
    treatment: JointTreatment,
) -> tuple[
    MemberExtensionSpecification,
    ...,
]:
    """Return physical extensions for a both-coped corner."""

    first_member = (
        treatment.joint.members[
            0
        ]
    )

    second_member = (
        treatment.joint.members[
            1
        ]
    )

    first_extension = (
        extension_to_outer_surface(
            first_member,
            second_member,
            treatment.joint,
        )
    )

    second_extension = (
        extension_to_outer_surface(
            second_member,
            first_member,
            treatment.joint,
        )
    )

    return (
        MemberExtensionSpecification(
            joint=treatment.joint,
            member=first_member,
            member_end=member_end_at_joint(
                first_member,
                treatment.joint,
            ),
            extension_mm=first_extension,
        ),
        MemberExtensionSpecification(
            joint=treatment.joint,
            member=second_member,
            member_end=member_end_at_joint(
                second_member,
                treatment.joint,
            ),
            extension_mm=second_extension,
        ),
    )


def extension_specifications_for_treatment(
    treatment: JointTreatment,
) -> tuple[
    MemberExtensionSpecification,
    ...,
]:
    """
    Return physical extension requirements for a treatment.

    AUTO:
        No explicit extension.

    MEMBER_THROUGH:
        Extend the selected through member.

    BOTH_COPED:
        Extend both corner members.

    THROUGH_PAIR:
        No extension. The two selected members already form
        the complete through path on opposite sides of the node.
    """

    if (
        treatment.mode
        == JointTreatmentMode.AUTO
    ):
        return ()

    if (
        treatment.mode
        == JointTreatmentMode.MEMBER_THROUGH
    ):
        return member_through_extensions(
            treatment
        )

    if (
        treatment.mode
        == JointTreatmentMode.BOTH_COPED
    ):
        return both_coped_extensions(
            treatment
        )

    if (
        treatment.mode
        == JointTreatmentMode.THROUGH_PAIR
    ):
        return ()

    raise ValueError(
        "Unsupported joint treatment mode."
    )
