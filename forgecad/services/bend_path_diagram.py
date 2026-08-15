"""2D bend-path diagram projection for ForgeCAD fabrication sheets."""

from dataclasses import dataclass
from math import ceil

from forgecad.services.bent_tube_path import (
    BentTubeCenterline,
    CircularArcPathSegment,
    StraightPathSegment,
)


@dataclass(frozen=True, slots=True)
class DiagramPoint:
    """A 2D point on a fabrication-sheet bend diagram."""

    x: float
    y: float


@dataclass(frozen=True, slots=True)
class DiagramSegment:
    """One projected centerline segment."""

    kind: str
    start: DiagramPoint
    end: DiagramPoint
    points: tuple[DiagramPoint, ...]


@dataclass(frozen=True, slots=True)
class BendPathDiagram:
    """A normalized 2D diagram of a bent-tube centerline."""

    segments: tuple[DiagramSegment, ...]
    width: float
    height: float
    axes: tuple[str, str]


def _project_point(
    point,
    axes,
):
    """Project one 3D point onto a selected pair of axes."""

    first, second = axes

    return DiagramPoint(
        float(
            getattr(
                point,
                first,
            )
        ),
        float(
            getattr(
                point,
                second,
            )
        ),
    )


def _arc_points_3d(
    segment,
    max_step_degrees=10.0,
):
    """Return sampled points along one exact 3D circular arc."""

    step = float(
        max_step_degrees
    )

    if step <= 0.0:
        raise ValueError(
            "Arc sample step must be greater than zero."
        )

    count = max(
        2,
        int(
            ceil(
                abs(
                    segment.angle_degrees
                )
                / step
            )
        ),
    )

    start_radius = (
        segment.center
        .vector_to(
            segment.start
        )
    )

    points = []

    for index in range(
        count + 1
    ):
        fraction = (
            index
            / count
        )

        rotated = (
            start_radius
            .rotated_about(
                segment.normal,
                segment.angle_degrees
                * fraction,
            )
        )

        points.append(
            segment.center.translate(
                rotated
            )
        )

    return tuple(
        points
    )


def _segment_points_3d(
    segment,
):
    """Return representative 3D points for one centerline segment."""

    if isinstance(
        segment,
        StraightPathSegment,
    ):
        return (
            segment.start,
            segment.end,
        )

    if isinstance(
        segment,
        CircularArcPathSegment,
    ):
        return _arc_points_3d(
            segment
        )

    raise TypeError(
        "Unsupported centerline segment."
    )


def _spread_for_axes(
    centerline,
    axes,
):
    """Return projected width and height for one axis pair."""

    points = [
        _project_point(
            point,
            axes,
        )
        for segment in centerline.segments
        for point in _segment_points_3d(
            segment
        )
    ]

    xs = [
        point.x
        for point in points
    ]
    ys = [
        point.y
        for point in points
    ]

    return (
        max(
            xs
        )
        - min(
            xs
        ),
        max(
            ys
        )
        - min(
            ys
        ),
    )


def best_projection_axes(
    centerline: BentTubeCenterline,
):
    """Choose the orthographic projection showing the most path spread."""

    if not isinstance(
        centerline,
        BentTubeCenterline,
    ):
        raise TypeError(
            "centerline must be a BentTubeCenterline instance."
        )

    candidates = (
        (
            "x",
            "y",
        ),
        (
            "x",
            "z",
        ),
        (
            "y",
            "z",
        ),
    )

    best = candidates[
        0
    ]
    best_area = -1.0

    for axes in candidates:
        width, height = (
            _spread_for_axes(
                centerline,
                axes,
            )
        )

        area = (
            width
            * height
        )

        if area > best_area:
            best = axes
            best_area = area

    return best


def build_bend_path_diagram(
    centerline: BentTubeCenterline,
    axes=None,
) -> BendPathDiagram:
    """
    Project a bent-tube centerline into normalized 2D diagram space.

    Circular arcs are sampled from the exact 3D arc before projection.
    This remains correct when a 3D circular bend projects as an ellipse.
    """

    if not isinstance(
        centerline,
        BentTubeCenterline,
    ):
        raise TypeError(
            "centerline must be a BentTubeCenterline instance."
        )

    if axes is None:
        axes = best_projection_axes(
            centerline
        )

    projected = []

    for segment in centerline.segments:
        if isinstance(
            segment,
            StraightPathSegment,
        ):
            kind = "straight"
        elif isinstance(
            segment,
            CircularArcPathSegment,
        ):
            kind = "arc"
        else:
            raise TypeError(
                "Unsupported centerline segment."
            )

        points = tuple(
            _project_point(
                point,
                axes,
            )
            for point in _segment_points_3d(
                segment
            )
        )

        projected.append(
            DiagramSegment(
                kind=kind,
                start=points[
                    0
                ],
                end=points[
                    -1
                ],
                points=points,
            )
        )

    all_x = [
        point.x
        for segment in projected
        for point in segment.points
    ]
    all_y = [
        point.y
        for segment in projected
        for point in segment.points
    ]

    min_x = min(
        all_x
    )
    min_y = min(
        all_y
    )

    normalized = tuple(
        DiagramSegment(
            kind=segment.kind,
            start=DiagramPoint(
                segment.start.x
                - min_x,
                segment.start.y
                - min_y,
            ),
            end=DiagramPoint(
                segment.end.x
                - min_x,
                segment.end.y
                - min_y,
            ),
            points=tuple(
                DiagramPoint(
                    point.x
                    - min_x,
                    point.y
                    - min_y,
                )
                for point in segment.points
            ),
        )
        for segment in projected
    )

    width = max(
        point.x
        for segment in normalized
        for point in segment.points
    )

    height = max(
        point.y
        for segment in normalized
        for point in segment.points
    )

    return BendPathDiagram(
        segments=normalized,
        width=width,
        height=height,
        axes=tuple(
            axes
        ),
    )
