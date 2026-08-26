"""Convert simple straight-member joints into bent-tube definitions."""

from dataclasses import dataclass
from math import (
    acos,
    degrees,
    radians,
    tan,
)

from forgecad.fabrication import (
    BentTube,
    Joint,
    Member,
)
from forgecad.geometry import (
    Point3D,
    Vector3D,
)
from forgecad.services.bent_tube_creation import (
    BendInput,
    BentTubeInput,
    create_bent_tube,
)


ANGLE_TOLERANCE_DEGREES = 1e-6
LENGTH_TOLERANCE_MM = 1e-6


@dataclass(frozen=True, slots=True)
class JointBendSpecification:
    """Describe one continuous bent tube derived from a simple joint."""

    joint: Joint
    first_member: Member
    second_member: Member
    start_node: object
    end_node: object
    bend_angle_degrees: float
    centerline_radius_mm: float
    tangent_setback_mm: float
    start_tangent: Point3D
    end_tangent: Point3D
    initial_direction: Vector3D
    bend_normal: Vector3D
    tube: BentTube


def _node_matches(
    first,
    second,
) -> bool:
    """Return True when two fabrication nodes occupy the same point."""

    return (
        float(first.x) == float(second.x)
        and float(first.y) == float(second.y)
        and float(first.z) == float(second.z)
    )


def outer_node_for_member(
    member: Member,
    joint: Joint,
):
    """Return the endpoint of a straight member opposite the joint node."""

    if not isinstance(
        member,
        Member,
    ):
        raise ValueError(
            "Convert Joint to Bend currently supports straight members only."
        )

    if _node_matches(
        member.start,
        joint.node,
    ):
        return member.end

    if _node_matches(
        member.end,
        joint.node,
    ):
        return member.start

    raise ValueError(
        "A selected member does not terminate at the supplied joint."
    )


def _vector_between_nodes(
    start,
    end,
) -> Vector3D:
    """Return a normalized direction from start to end."""

    vector = Vector3D(
        float(end.x) - float(start.x),
        float(end.y) - float(start.y),
        float(end.z) - float(start.z),
    )

    if vector.magnitude <= LENGTH_TOLERANCE_MM:
        raise ValueError(
            "Cannot create a bend from a zero-length member."
        )

    return vector.normalized()


def _point_from_node(
    node,
) -> Point3D:
    """Return a Point3D from a fabrication node."""

    return Point3D(
        float(node.x),
        float(node.y),
        float(node.z),
    )


def _point_along(
    start,
    direction: Vector3D,
    distance: float,
) -> Point3D:
    """Return a point translated from start along direction."""

    return Point3D(
        float(start.x)
        + float(direction.x) * float(distance),
        float(start.y)
        + float(direction.y) * float(distance),
        float(start.z)
        + float(direction.z) * float(distance),
    )


def bend_angle_between_members(
    first_member: Member,
    second_member: Member,
    joint: Joint,
) -> float:
    """
    Return the physical bend deflection between two straight members.

    Member rays are measured outward from the theoretical joint. A tube
    traveling into the joint along the first member therefore approaches
    opposite the first outward ray. The bend deflection is consequently:

        bend angle = 180 degrees - outward included angle
    """

    first_outer = outer_node_for_member(
        first_member,
        joint,
    )

    second_outer = outer_node_for_member(
        second_member,
        joint,
    )

    first_outward = _vector_between_nodes(
        joint.node,
        first_outer,
    )

    second_outward = _vector_between_nodes(
        joint.node,
        second_outer,
    )

    dot = max(
        -1.0,
        min(
            1.0,
            first_outward.dot(
                second_outward
            ),
        ),
    )

    included_angle = degrees(
        acos(
            dot
        )
    )

    bend_angle = (
        180.0
        - included_angle
    )

    if (
        bend_angle <= ANGLE_TOLERANCE_DEGREES
        or bend_angle
        >= 180.0 - ANGLE_TOLERANCE_DEGREES
    ):
        raise ValueError(
            "Cannot convert collinear members into a practical bend."
        )

    return bend_angle


def tangent_setback(
    centerline_radius_mm: float,
    bend_angle_degrees: float,
) -> float:
    """
    Return the tangent setback from theoretical intersection to tangent point.

        setback = CLR * tan(bend angle / 2)
    """

    radius = float(
        centerline_radius_mm
    )

    if radius <= 0.0:
        raise ValueError(
            "Bend centerline radius must be greater than zero."
        )

    angle = float(
        bend_angle_degrees
    )

    if (
        angle <= ANGLE_TOLERANCE_DEGREES
        or angle
        >= 180.0 - ANGLE_TOLERANCE_DEGREES
    ):
        raise ValueError(
            "Bend angle must be greater than 0 and less than 180 degrees."
        )

    return radius * tan(
        radians(
            angle / 2.0
        )
    )


def bend_specification_from_joint(
    joint: Joint,
    centerline_radius_mm: float,
    name: str = "Bent Joint",
) -> JointBendSpecification:
    """
    Build one continuous bent-tube definition from a simple straight joint.

    The original joint node remains the theoretical design intersection.
    The physical tube is tangent to both member centerlines before reaching
    that intersection.
    """

    if not isinstance(
        joint,
        Joint,
    ):
        raise TypeError(
            "joint must be a Joint instance."
        )

    if not joint.is_simple:
        raise ValueError(
            "Convert Joint to Bend requires exactly two members."
        )

    first_member = joint.members[
        0
    ]

    second_member = joint.members[
        1
    ]

    if (
        not isinstance(
            first_member,
            Member,
        )
        or not isinstance(
            second_member,
            Member,
        )
    ):
        raise ValueError(
            "Convert Joint to Bend currently supports two straight members only."
        )

    if first_member.profile != second_member.profile:
        raise ValueError(
            "Both members must use the same tube profile."
        )

    if first_member.material != second_member.material:
        raise ValueError(
            "Both members must use the same material."
        )

    first_outer = outer_node_for_member(
        first_member,
        joint,
    )

    second_outer = outer_node_for_member(
        second_member,
        joint,
    )

    bend_angle = bend_angle_between_members(
        first_member,
        second_member,
        joint,
    )

    setback = tangent_setback(
        centerline_radius_mm,
        bend_angle,
    )

    first_length = float(
        first_member.length
    )

    second_length = float(
        second_member.length
    )

    if first_length <= setback + LENGTH_TOLERANCE_MM:
        raise ValueError(
            "First member is too short for the requested bend radius."
        )

    if second_length <= setback + LENGTH_TOLERANCE_MM:
        raise ValueError(
            "Second member is too short for the requested bend radius."
        )

    start_run_length = (
        first_length
        - setback
    )

    end_run_length = (
        second_length
        - setback
    )

    initial_direction = _vector_between_nodes(
        first_outer,
        joint.node,
    )

    outgoing_direction = _vector_between_nodes(
        joint.node,
        second_outer,
    )

    bend_normal = initial_direction.cross(
        outgoing_direction
    )

    if bend_normal.magnitude <= 1e-12:
        raise ValueError(
            "Cannot determine a bend plane from collinear members."
        )

    bend_normal = bend_normal.normalized()

    first_outward = _vector_between_nodes(
        joint.node,
        first_outer,
    )

    second_outward = _vector_between_nodes(
        joint.node,
        second_outer,
    )

    start_tangent = _point_along(
        joint.node,
        first_outward,
        setback,
    )

    end_tangent = _point_along(
        joint.node,
        second_outward,
        setback,
    )

    definition = BentTubeInput(
        name=name,
        run_lengths=(
            start_run_length,
            end_run_length,
        ),
        bends=(
            BendInput(
                angle_degrees=bend_angle,
                centerline_radius=float(
                    centerline_radius_mm
                ),
                rotation_degrees=0.0,
            ),
        ),
    )

    tube = create_bent_tube(
        definition,
        first_member.profile,
        first_member.material,
    )

    return JointBendSpecification(
        joint=joint,
        first_member=first_member,
        second_member=second_member,
        start_node=first_outer,
        end_node=second_outer,
        bend_angle_degrees=bend_angle,
        centerline_radius_mm=float(
            centerline_radius_mm
        ),
        tangent_setback_mm=setback,
        start_tangent=start_tangent,
        end_tangent=end_tangent,
        initial_direction=initial_direction,
        bend_normal=bend_normal,
        tube=tube,
    )
