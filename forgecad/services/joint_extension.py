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
    member_contains_node_interior,
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


def member_through_extension(
    intersecting_member: Member,
) -> float:
    """
    Return the physical extension for a selected through member.

    A through tube continues from the design node to the outside
    surface of the intersecting tube.

    This is a physical end extension, not a projected tangent
    distance along the joint angle.
    """

    return (
        float(
            intersecting_member
            .profile
            .outside_diameter
        )
        / 2.0
    )


def extension_to_outer_surface(
    extended_member: Member,
    intersecting_member: Member,
    joint: Joint,
) -> float:
    """
    Return angle-corrected stock required for a miter.

    This calculation is appropriate when stock must reach the
    complete projected outer surface before being trimmed by an
    angled shared plane.

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
            intersecting_member
            .profile
            .outside_diameter
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
    """
    Return extension for the selected through member only.

    Only the selected through tube receives a real physical
    extension. Coped members retain their design endpoints.

    When the selected through member already passes through the
    joint as one continuous physical member, no end extension is
    required.
    """

    joint = treatment.joint

    through_member = (
        treatment.through_members[
            0
        ]
    )

    if member_contains_node_interior(
        through_member,
        joint.node,
    ):
        return ()

    other_members = [
        member
        for member in joint.members
        if member is not through_member
    ]

    if not other_members:
        return ()

    extension = max(
        member_through_extension(
            other_member
        )
        for other_member
        in other_members
    )

    return (
        MemberExtensionSpecification(
            joint=joint,
            member=through_member,
            member_end=member_end_at_joint(
                through_member,
                joint,
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
    """
    Return stock extensions for a mitered corner.

    BOTH_COPED remains the persistence-compatible internal
    name for the user-facing Both Mitered treatment.
    """

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
    """Return physical member extensions required by a treatment."""

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
