"""Pure 3D centerline construction for ForgeCAD bent tubes."""

from dataclasses import dataclass

from forgecad.fabrication import (
    Bend,
    BentTube,
)
from forgecad.geometry import (
    Point3D,
    Vector3D,
)


@dataclass(frozen=True, slots=True)
class StraightPathSegment:
    """One straight centerline segment."""

    start: Point3D
    end: Point3D

    @property
    def length(self) -> float:
        """Return straight segment length."""

        return (
            self.start
            .vector_to(
                self.end
            )
            .magnitude
        )


@dataclass(frozen=True, slots=True)
class CircularArcPathSegment:
    """One circular centerline bend arc."""

    start: Point3D
    end: Point3D
    center: Point3D
    normal: Vector3D
    radius_mm: float
    angle_degrees: float


@dataclass(frozen=True, slots=True)
class BentTubeCenterline:
    """Ordered 3D centerline primitives for one physical bent tube."""

    segments: tuple[
        StraightPathSegment | CircularArcPathSegment,
        ...,
    ]
    start_point: Point3D
    end_point: Point3D
    end_direction: Vector3D

    @property
    def segment_count(self) -> int:
        """Return number of centerline primitives."""

        return len(
            self.segments
        )


def _point_plus_vector(
    point: Point3D,
    vector: Vector3D,
) -> Point3D:
    """Translate a point by a vector."""

    return point.translate(
        vector
    )


def _normalized_perpendicular(
    vector: Vector3D,
    reference: Vector3D,
) -> Vector3D:
    """Return a normalized reference component perpendicular to vector."""

    direction = vector.normalized()

    perpendicular = reference.minus(
        direction.scaled(
            reference.dot(
                direction
            )
        )
    )

    if perpendicular.magnitude <= 1e-12:
        raise ValueError(
            "Initial bend normal cannot be parallel to tube direction."
        )

    return perpendicular.normalized()


def _arc_from_tangent(
    start_point: Point3D,
    incoming_direction: Vector3D,
    bend: Bend,
    plane_normal: Vector3D,
):
    """Construct one tangent circular arc and its outgoing direction."""

    direction = incoming_direction.normalized()
    normal = _normalized_perpendicular(
        direction,
        plane_normal,
    )

    radius_direction = normal.cross(
        direction
    ).normalized()

    center = _point_plus_vector(
        start_point,
        radius_direction.scaled(
            bend.centerline_radius
        ),
    )

    start_radius = center.vector_to(
        start_point
    )

    end_radius = start_radius.rotated_about(
        normal,
        bend.angle_degrees,
    )

    end_point = _point_plus_vector(
        center,
        end_radius,
    )

    outgoing_direction = direction.rotated_about(
        normal,
        bend.angle_degrees,
    ).normalized()

    return (
        CircularArcPathSegment(
            start=start_point,
            end=end_point,
            center=center,
            normal=normal,
            radius_mm=(
                bend.centerline_radius
            ),
            angle_degrees=(
                bend.angle_degrees
            ),
        ),
        outgoing_direction,
        normal,
    )


def build_bent_tube_centerline(
    tube: BentTube,
    start_point: Point3D = Point3D(
        0.0,
        0.0,
        0.0,
    ),
    initial_direction: Vector3D = Vector3D(
        1.0,
        0.0,
        0.0,
    ),
    initial_bend_normal: Vector3D = Vector3D(
        0.0,
        0.0,
        1.0,
    ),
) -> BentTubeCenterline:
    """
    Build the true 3D centerline of a physical bent tube.

    The first straight run begins at start_point along initial_direction.

    Each Bend.rotation_degrees clocks that bend plane around the current
    incoming tube direction relative to the previous bend plane.
    """

    if not isinstance(
        tube,
        BentTube,
    ):
        raise TypeError(
            "tube must be a BentTube instance."
        )

    if not isinstance(
        start_point,
        Point3D,
    ):
        raise TypeError(
            "start_point must be a Point3D instance."
        )

    direction = initial_direction.normalized()

    reference_normal = _normalized_perpendicular(
        direction,
        initial_bend_normal,
    )

    current_point = start_point
    segments = []

    for bend_index, bend in enumerate(
        tube.bends
    ):
        run = tube.straight_runs[
            bend_index
        ]

        straight_end = _point_plus_vector(
            current_point,
            direction.scaled(
                run.length_mm
            ),
        )

        segments.append(
            StraightPathSegment(
                start=current_point,
                end=straight_end,
            )
        )

        current_point = straight_end

        bend_normal = reference_normal.rotated_about(
            direction,
            bend.rotation_degrees,
        ).normalized()

        (
            arc,
            direction,
            reference_normal,
        ) = _arc_from_tangent(
            current_point,
            direction,
            bend,
            bend_normal,
        )

        segments.append(
            arc
        )

        current_point = (
            arc.end
        )

    final_run = tube.straight_runs[
        -1
    ]

    final_point = _point_plus_vector(
        current_point,
        direction.scaled(
            final_run.length_mm
        ),
    )

    segments.append(
        StraightPathSegment(
            start=current_point,
            end=final_point,
        )
    )

    return BentTubeCenterline(
        segments=tuple(
            segments
        ),
        start_point=start_point,
        end_point=final_point,
        end_direction=direction,
    )
