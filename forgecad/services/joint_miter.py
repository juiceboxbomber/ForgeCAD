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


def member_end_at_joint(member, joint) -> str:
    """Return which structural-member end occupies a joint."""
    from forgecad.services.node_proximity import nodes_coincident

    if nodes_coincident(member.start, joint.node):
        return MITER_END_START
    if nodes_coincident(member.end, joint.node):
        return MITER_END_END
    raise ValueError("Member does not touch the supplied joint.")



def member_direction_from_joint(member, joint) -> Vector3:
    """Return the unit direction from a joint into a member."""
    from forgecad.services.joint_geometry import member_direction_from_node

    x, y, z = member_direction_from_node(member, joint.node)
    return Vector3(float(x), float(y), float(z)).normalized()



def member_keep_point(
    member,
    joint,
) -> tuple[
    float,
    float,
    float,
]:
    """
    Return a point on the member side that must survive a miter cut.

    Straight members may safely use the opposite endpoint because their whole
    centerline stays on one side of an endpoint miter plane.

    Bent members must NOT use the opposite endpoint: after one or more bends
    that distant endpoint may lie on the other side of the local miter plane.
    Use a short point along the true inward endpoint tangent instead.
    """

    from forgecad.fabrication import (
        BentMember,
    )
    from forgecad.services.node_proximity import (
        nodes_coincident,
    )

    if isinstance(
        member,
        BentMember,
    ):
        direction = (
            member_direction_from_joint(
                member,
                joint,
            )
        )

        outside_diameter = float(
            member.profile.outside_diameter
        )

        if nodes_coincident(
            member.start,
            joint.node,
        ):
            run_length = float(
                member.tube.straight_runs[
                    0
                ].length_mm
            )
        elif nodes_coincident(
            member.end,
            joint.node,
        ):
            run_length = float(
                member.tube.straight_runs[
                    -1
                ].length_mm
            )
        else:
            raise ValueError(
                "Member does not touch the supplied joint."
            )

        # Any positive distance chooses the correct half-space. Keep it local
        # to the endpoint so the point still describes this end even on a
        # short terminal straight run.
        local_distance = min(
            max(
                outside_diameter,
                1.0,
            ),
            max(
                run_length * 0.5,
                1.0,
            ),
        )

        return (
            float(
                joint.node.x
            )
            + direction.x
            * local_distance,
            float(
                joint.node.y
            )
            + direction.y
            * local_distance,
            float(
                joint.node.z
            )
            + direction.z
            * local_distance,
        )

    if nodes_coincident(
        member.start,
        joint.node,
    ):
        keep = member.end

    elif nodes_coincident(
        member.end,
        joint.node,
    ):
        keep = member.start

    else:
        raise ValueError(
            "Member does not touch the supplied joint."
        )

    return (
        float(keep.x),
        float(keep.y),
        float(keep.z),
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

    miter_members = (
        treatment.coped_members
    )

    if (
        len(
            miter_members
        )
        != 2
    ):
        raise ValueError(
            "A both-mitered treatment requires "
            "exactly two selected members."
        )

    first_member = (
        miter_members[
            0
        ]
    )

    second_member = (
        miter_members[
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
