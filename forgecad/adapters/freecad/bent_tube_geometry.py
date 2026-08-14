"""FreeCAD geometry adapter for ForgeCAD bent tubes."""

import FreeCAD
import Part

from forgecad.services.bent_tube_path import (
    CircularArcPathSegment,
    StraightPathSegment,
    build_bent_tube_centerline,
)


def point_vector(point):
    """Convert a ForgeCAD Point3D to a FreeCAD vector."""

    return FreeCAD.Vector(
        point.x,
        point.y,
        point.z,
    )


def vector3d_vector(vector):
    """Convert a ForgeCAD Vector3D to a FreeCAD vector."""

    return FreeCAD.Vector(
        vector.x,
        vector.y,
        vector.z,
    )


def build_centerline_edge(segment):
    """Build one FreeCAD edge from a ForgeCAD centerline segment."""

    if isinstance(
        segment,
        StraightPathSegment,
    ):
        return Part.makeLine(
            point_vector(
                segment.start
            ),
            point_vector(
                segment.end
            ),
        )

    if isinstance(
        segment,
        CircularArcPathSegment,
    ):
        start = point_vector(
            segment.start
        )
        end = point_vector(
            segment.end
        )
        center = point_vector(
            segment.center
        )

        start_radius = (
            start - center
        )

        midpoint_radius = FreeCAD.Rotation(
            vector3d_vector(
                segment.normal
            ),
            segment.angle_degrees / 2.0,
        ).multVec(
            start_radius
        )

        midpoint = (
            center
            + midpoint_radius
        )

        return Part.Arc(
            start,
            midpoint,
            end,
        ).toShape()

    raise TypeError(
        "Unsupported bent-tube centerline segment."
    )


def build_centerline_wire(centerline):
    """Build one continuous FreeCAD wire from centerline primitives."""

    edges = [
        build_centerline_edge(
            segment
        )
        for segment in centerline.segments
    ]

    if not edges:
        raise ValueError(
            "Bent-tube centerline contains no segments."
        )

    return Part.Wire(
        edges
    )


def _profile_wire(
    point,
    direction,
    radius,
):
    """Build a circular profile wire normal to the path direction."""

    edge = Part.makeCircle(
        radius,
        point_vector(
            point
        ),
        vector3d_vector(
            direction
        ),
    )

    return Part.Wire(
        [
            edge
        ]
    )


def _swept_solid(
    path_wire,
    profile_wire,
):
    """Sweep a closed circular profile along a centerline wire."""

    return path_wire.makePipeShell(
        [
            profile_wire
        ],
        True,
        False,
    )


def build_bent_tube_shape(
    tube,
    start_point=None,
    initial_direction=None,
    initial_bend_normal=None,
):
    """Build one continuous hollow FreeCAD solid for a ForgeCAD BentTube."""

    kwargs = {}

    if start_point is not None:
        kwargs[
            "start_point"
        ] = start_point

    if initial_direction is not None:
        kwargs[
            "initial_direction"
        ] = initial_direction

    if initial_bend_normal is not None:
        kwargs[
            "initial_bend_normal"
        ] = initial_bend_normal

    centerline = build_bent_tube_centerline(
        tube,
        **kwargs,
    )

    path_wire = build_centerline_wire(
        centerline
    )

    outer_radius = (
        tube.profile.outside_diameter
        / 2.0
    )
    inner_radius = (
        tube.profile.inside_diameter
        / 2.0
    )

    outer_profile = _profile_wire(
        centerline.start_point,
        centerline.segments[
            0
        ].start.vector_to(
            centerline.segments[
                0
            ].end
        ).normalized(),
        outer_radius,
    )

    inner_profile = _profile_wire(
        centerline.start_point,
        centerline.segments[
            0
        ].start.vector_to(
            centerline.segments[
                0
            ].end
        ).normalized(),
        inner_radius,
    )

    outer_solid = _swept_solid(
        path_wire,
        outer_profile,
    )

    inner_solid = _swept_solid(
        path_wire,
        inner_profile,
    )

    return (
        outer_solid.cut(
            inner_solid
        ),
        centerline,
    )
