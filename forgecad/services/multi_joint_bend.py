"""Build continuous bent tubes from ordered design nodes."""

from math import (
    acos,
    atan2,
    degrees,
    radians,
    tan,
)

from forgecad.fabrication import (
    Bend,
    BentTube,
    StraightRun,
)
from forgecad.geometry import (
    Vector3D,
)


ANGLE_TOLERANCE_DEGREES = 1e-6
LENGTH_TOLERANCE_MM = 1e-6
VECTOR_TOLERANCE = 1e-12


def _vector_between_nodes(
    start,
    end,
) -> Vector3D:
    """Return the normalized direction from one node to another."""

    vector = Vector3D(
        float(end.x) - float(start.x),
        float(end.y) - float(start.y),
        float(end.z) - float(start.z),
    )

    if (
        vector.magnitude
        <= LENGTH_TOLERANCE_MM
    ):
        raise ValueError(
            "Design nodes must not occupy the same point."
        )

    return vector.normalized()


def _segment_length(
    start,
    end,
) -> float:
    """Return straight-line distance between two design nodes."""

    dx = (
        float(end.x)
        - float(start.x)
    )

    dy = (
        float(end.y)
        - float(start.y)
    )

    dz = (
        float(end.z)
        - float(start.z)
    )

    return (
        dx * dx
        + dy * dy
        + dz * dz
    ) ** 0.5


def _bend_angle(
    previous_node,
    joint_node,
    next_node,
) -> float:
    """
    Return physical tube deflection at one theoretical design joint.

    The two rays are measured outward from the joint. The physical tube
    approaches the joint opposite the incoming outward ray, so:

        bend angle = 180 degrees - outward included angle
    """

    incoming_outward = (
        _vector_between_nodes(
            joint_node,
            previous_node,
        )
    )

    outgoing_outward = (
        _vector_between_nodes(
            joint_node,
            next_node,
        )
    )

    dot = max(
        -1.0,
        min(
            1.0,
            incoming_outward.dot(
                outgoing_outward
            ),
        ),
    )

    included_angle = degrees(
        acos(
            dot
        )
    )

    angle = (
        180.0
        - included_angle
    )

    if (
        angle
        <= ANGLE_TOLERANCE_DEGREES
        or angle
        >= (
            180.0
            - ANGLE_TOLERANCE_DEGREES
        )
    ):
        raise ValueError(
            "Design joint cannot produce a practical bend."
        )

    return angle


def _bend_normal(
    previous_node,
    joint_node,
    next_node,
) -> Vector3D:
    """
    Return the oriented normal of one bend plane.

    The normal follows the actual travel direction through the joint:

        incoming direction cross outgoing direction

    Reversing the turn therefore reverses the normal, which becomes
    a 180-degree clocking change for the following bend.
    """

    incoming_direction = (
        _vector_between_nodes(
            previous_node,
            joint_node,
        )
    )

    outgoing_direction = (
        _vector_between_nodes(
            joint_node,
            next_node,
        )
    )

    normal = incoming_direction.cross(
        outgoing_direction
    )

    if (
        normal.magnitude
        <= VECTOR_TOLERANCE
    ):
        raise ValueError(
            "Design joint cannot determine a bend plane."
        )

    return normal.normalized()


def _signed_rotation_about_axis(
    previous_normal: Vector3D,
    current_normal: Vector3D,
    axis: Vector3D,
) -> float:
    """
    Return signed degrees from previous_normal to current_normal about axis.

    Both bend-plane normals are perpendicular to the tube direction at the
    shared straight run. atan2 preserves whether the required clocking is
    positive or negative and correctly handles 90- and 180-degree changes.
    """

    axis = axis.normalized()
    previous_normal = previous_normal.normalized()
    current_normal = current_normal.normalized()

    cosine = max(
        -1.0,
        min(
            1.0,
            previous_normal.dot(
                current_normal
            ),
        ),
    )

    sine = axis.dot(
        previous_normal.cross(
            current_normal
        )
    )

    angle = degrees(
        atan2(
            sine,
            cosine,
        )
    )

    # Avoid storing meaningless floating-point noise for coplanar,
    # same-direction bends.
    if (
        abs(
            angle
        )
        <= ANGLE_TOLERANCE_DEGREES
    ):
        return 0.0

    return angle


def _bend_rotations(
    nodes,
) -> tuple[float, ...]:
    """
    Return bend-plane clocking values in path order.

    Bend 1 establishes the initial bend plane and therefore has zero
    relative rotation. Every later bend is clocked from the preceding
    bend plane around the straight-run direction connecting the joints.
    """

    bend_count = (
        len(
            nodes
        )
        - 2
    )

    normals = tuple(
        _bend_normal(
            nodes[index],
            nodes[index + 1],
            nodes[index + 2],
        )
        for index in range(
            bend_count
        )
    )

    rotations = [
        0.0
    ]

    for index in range(
        1,
        bend_count,
    ):
        incoming_direction = (
            _vector_between_nodes(
                nodes[index],
                nodes[index + 1],
            )
        )

        rotations.append(
            _signed_rotation_about_axis(
                normals[index - 1],
                normals[index],
                incoming_direction,
            )
        )

    return tuple(
        rotations
    )


def _tangent_setback(
    radius_mm,
    bend_angle_degrees,
) -> float:
    """Return tangent setback for one bend."""

    radius = float(
        radius_mm
    )

    if radius <= 0.0:
        raise ValueError(
            "Bend radius must be greater than zero."
        )

    angle = float(
        bend_angle_degrees
    )

    return radius * tan(
        radians(
            angle / 2.0
        )
    )


def build_multi_joint_bent_tube(
    nodes,
    centerline_radii_mm,
    profile,
    material,
) -> BentTube:
    """
    Build a continuous BentTube from ordered theoretical design nodes.

    For N design nodes there are:

        N - 1 design segments
        N - 2 bends

    Each bend removes its tangent setback from both adjacent design
    segments. A middle straight run is therefore shortened by the
    setbacks of both neighboring bends.

    Bend rotations are calculated from the actual ordered design geometry.
    The first bend establishes the initial bend plane at zero rotation.
    Each later bend stores its relative clocking around the incoming tube
    direction from the preceding bend plane.

    Node order must follow the fabricated tube from start to end.
    """

    nodes = tuple(
        nodes
    )

    radii = tuple(
        float(radius)
        for radius
        in centerline_radii_mm
    )

    if len(
        nodes
    ) < 3:
        raise ValueError(
            "A bent tube requires at least three design nodes."
        )

    bend_count = (
        len(nodes)
        - 2
    )

    if len(
        radii
    ) != bend_count:
        raise ValueError(
            "A bend radius is required for each design joint."
        )

    segment_lengths = [
        _segment_length(
            nodes[index],
            nodes[index + 1],
        )
        for index
        in range(
            len(nodes) - 1
        )
    ]

    bend_angles = tuple(
        _bend_angle(
            nodes[index],
            nodes[index + 1],
            nodes[index + 2],
        )
        for index
        in range(
            bend_count
        )
    )

    bend_rotations = (
        _bend_rotations(
            nodes
        )
    )

    setbacks = tuple(
        _tangent_setback(
            radii[index],
            bend_angles[index],
        )
        for index
        in range(
            bend_count
        )
    )

    bends = tuple(
        Bend(
            angle_degrees=bend_angles[index],
            centerline_radius=radii[index],
            rotation_degrees=bend_rotations[index],
        )
        for index
        in range(
            bend_count
        )
    )

    run_lengths = []

    for index, segment_length in enumerate(
        segment_lengths
    ):
        start_setback = (
            setbacks[
                index - 1
            ]
            if index > 0
            else 0.0
        )

        end_setback = (
            setbacks[
                index
            ]
            if index < bend_count
            else 0.0
        )

        run_length = (
            segment_length
            - start_setback
            - end_setback
        )

        if (
            run_length
            <= LENGTH_TOLERANCE_MM
        ):
            raise ValueError(
                "A design segment is too short for "
                "the requested bend radius."
            )

        run_lengths.append(
            run_length
        )

    return BentTube(
        straight_runs=tuple(
            StraightRun(
                length
            )
            for length
            in run_lengths
        ),
        bends=bends,
        profile=profile,
        material=material,
    )
