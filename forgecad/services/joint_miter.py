"""Miter analysis for ForgeCAD tube joints."""

from dataclasses import dataclass
from math import sqrt

from forgecad.fabrication import (
    Joint,
    Member,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
    JointTreatmentMode,
)


MITER_END_START = "start"
MITER_END_END = "end"


@dataclass(frozen=True, slots=True)
class Vector3:
    """Simple geometry vector independent of FreeCAD."""

    x: float
    y: float
    z: float

    @property
    def length(self) -> float:
        """Return vector magnitude."""

        return sqrt(
            self.x * self.x
            + self.y * self.y
            + self.z * self.z
        )

    def normalized(self):
        """Return a unit-length vector."""

        length = self.length

        if length <= 1e-12:
            raise ValueError(
                "Cannot normalize a zero-length vector."
            )

        return Vector3(
            self.x / length,
            self.y / length,
            self.z / length,
        )


@dataclass(frozen=True, slots=True)
class MiterSpecification:
    """Describe one member end trimmed by a shared miter plane."""

    joint: Joint
    member: Member

    member_end: str

    plane_point: tuple[
        float,
        float,
        float,
    ]

    plane_normal: tuple[
        float,
        float,
        float,
    ]

    keep_point: tuple[
        float,
        float,
        float,
    ]


def member_end_at_joint(
    member: Member,
    joint: Joint,
) -> str:
    """Return which member end lies at the supplied joint."""

    if member.start == joint.node:
        return MITER_END_START

    if member.end == joint.node:
        return MITER_END_END

    raise ValueError(
        "Member does not touch the supplied joint."
    )


def member_direction_from_joint(
    member: Member,
    joint: Joint,
) -> Vector3:
    """Return member direction pointing away from the joint."""

    if member.start == joint.node:
        other = member.end

    elif member.end == joint.node:
        other = member.start

    else:
        raise ValueError(
            "Member does not touch the supplied joint."
        )

    return Vector3(
        float(
            other.x - joint.node.x
        ),
        float(
            other.y - joint.node.y
        ),
        float(
            other.z - joint.node.z
        ),
    ).normalized()


def member_keep_point(
    member: Member,
    joint: Joint,
) -> tuple[
    float,
    float,
    float,
]:
    """Return the member endpoint away from the joint."""

    if member.start == joint.node:
        node = member.end

    elif member.end == joint.node:
        node = member.start

    else:
        raise ValueError(
            "Member does not touch the supplied joint."
        )

    return (
        float(node.x),
        float(node.y),
        float(node.z),
    )


def equal_miter_plane_normal(
    first_member: Member,
    second_member: Member,
    joint: Joint,
) -> tuple[
    float,
    float,
    float,
]:
    """
    Return the normal of the shared equal-angle miter plane.

    The member directions point away from the joint.

    Their sum follows the internal angle bisector, which is
    the direction of the miter plane itself.

    The plane normal is therefore formed from the difference
    of the two unit member directions.
    """

    first_direction = (
        member_direction_from_joint(
            first_member,
            joint,
        )
    )

    second_direction = (
        member_direction_from_joint(
            second_member,
            joint,
        )
    )

    normal_vector = Vector3(
        first_direction.x
        - second_direction.x,
        first_direction.y
        - second_direction.y,
        first_direction.z
        - second_direction.z,
    )

    if normal_vector.length <= 1e-12:
        raise ValueError(
            "Cannot create an equal miter for "
            "parallel members pointing in the same direction."
        )

    normal = (
        normal_vector.normalized()
    )

    return (
        normal.x,
        normal.y,
        normal.z,
    )


def both_mitered_specifications(
    treatment: JointTreatment,
) -> tuple[
    MiterSpecification,
    ...,
]:
    """Return the two trims required for a mitered corner."""

    joint = treatment.joint

    if joint.member_count != 2:
        raise ValueError(
            "A both-mitered treatment requires "
            "exactly two members."
        )

    first_member = (
        joint.members[
            0
        ]
    )

    second_member = (
        joint.members[
            1
        ]
    )

    plane_normal = (
        equal_miter_plane_normal(
            first_member,
            second_member,
            joint,
        )
    )

    plane_point = (
        float(joint.node.x),
        float(joint.node.y),
        float(joint.node.z),
    )

    return (
        MiterSpecification(
            joint=joint,
            member=first_member,
            member_end=member_end_at_joint(
                first_member,
                joint,
            ),
            plane_point=plane_point,
            plane_normal=plane_normal,
            keep_point=member_keep_point(
                first_member,
                joint,
            ),
        ),
        MiterSpecification(
            joint=joint,
            member=second_member,
            member_end=member_end_at_joint(
                second_member,
                joint,
            ),
            plane_point=plane_point,
            plane_normal=plane_normal,
            keep_point=member_keep_point(
                second_member,
                joint,
            ),
        ),
    )


def miter_specifications_for_treatment(
    treatment: JointTreatment,
) -> tuple[
    MiterSpecification,
    ...,
]:
    """
    Return miter specifications for a joint treatment.

    BOTH_COPED is retained as the persistence-compatible
    internal value for the user-facing Both Mitered treatment.
    """

    if (
        treatment.mode
        == JointTreatmentMode.BOTH_COPED
    ):
        return both_mitered_specifications(
            treatment
        )

    return ()
