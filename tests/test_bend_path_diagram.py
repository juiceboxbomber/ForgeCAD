"""Tests for ForgeCAD bend-path diagram projection."""

import pytest

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.services.bend_path_diagram import (
    best_projection_axes,
    build_bend_path_diagram,
)
from forgecad.services.bent_tube_path import (
    build_bent_tube_centerline,
)


def _material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def _profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def _planar_tube():
    return BentTube(
        straight_runs=(
            StraightRun(
                500.0
            ),
            StraightRun(
                500.0
            ),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


def _three_dimensional_tube():
    return BentTube(
        straight_runs=(
            StraightRun(
                500.0
            ),
            StraightRun(
                500.0
            ),
            StraightRun(
                500.0
            ),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
                rotation_degrees=0.0,
            ),
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
                rotation_degrees=90.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


def test_planar_xy_tube_prefers_xy_projection():
    centerline = build_bent_tube_centerline(
        _planar_tube()
    )

    assert best_projection_axes(
        centerline
    ) == (
        "x",
        "y",
    )


def test_diagram_preserves_segment_order_and_kind():
    centerline = build_bent_tube_centerline(
        _planar_tube()
    )

    diagram = build_bend_path_diagram(
        centerline
    )

    assert [
        segment.kind
        for segment in diagram.segments
    ] == [
        "straight",
        "arc",
        "straight",
    ]


def test_planar_90_degree_arc_has_sampled_curve_points():
    centerline = build_bent_tube_centerline(
        _planar_tube()
    )

    diagram = build_bend_path_diagram(
        centerline,
        axes=(
            "x",
            "y",
        ),
    )

    arc = diagram.segments[
        1
    ]

    assert arc.kind == "arc"
    assert len(
        arc.points
    ) > 3

    midpoint = arc.points[
        len(
            arc.points
        )
        // 2
    ]

    chord_mid_x = (
        arc.start.x
        + arc.end.x
    ) / 2.0
    chord_mid_y = (
        arc.start.y
        + arc.end.y
    ) / 2.0

    assert (
        abs(
            midpoint.x
            - chord_mid_x
        )
        > 1.0
        or abs(
            midpoint.y
            - chord_mid_y
        )
        > 1.0
    )


def test_arc_samples_preserve_exact_projected_endpoints():
    centerline = build_bent_tube_centerline(
        _planar_tube()
    )

    diagram = build_bend_path_diagram(
        centerline,
        axes=(
            "x",
            "y",
        ),
    )

    arc = diagram.segments[
        1
    ]

    assert arc.points[
        0
    ] == arc.start
    assert arc.points[
        -1
    ] == arc.end


def test_diagram_is_normalized_using_all_curve_points():
    centerline = build_bent_tube_centerline(
        _planar_tube()
    )

    diagram = build_bend_path_diagram(
        centerline
    )

    min_x = min(
        point.x
        for segment in diagram.segments
        for point in segment.points
    )

    min_y = min(
        point.y
        for segment in diagram.segments
        for point in segment.points
    )

    assert min_x == pytest.approx(
        0.0
    )
    assert min_y == pytest.approx(
        0.0
    )


def test_three_dimensional_tube_keeps_curved_projected_bends():
    centerline = build_bent_tube_centerline(
        _three_dimensional_tube()
    )

    diagram = build_bend_path_diagram(
        centerline
    )

    arcs = [
        segment
        for segment in diagram.segments
        if segment.kind
        == "arc"
    ]

    assert len(
        arcs
    ) == 2

    assert all(
        len(
            arc.points
        )
        > 3
        for arc in arcs
    )

    assert diagram.width > 0.0
    assert diagram.height > 0.0
