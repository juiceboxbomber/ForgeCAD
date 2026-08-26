"""Tests for deriving multi-bend tube geometry from design joints."""

import pytest

from forgecad.fabrication import (
    Material,
    Node,
    TubeProfile,
)
from forgecad.services.multi_joint_bend import (
    build_multi_joint_bent_tube,
)


def _profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def _material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def test_two_90_degree_corners_create_two_bends():
    """
    Four design points define three straight design segments
    and therefore two physical bends.
    """

    start = Node(
        0.0,
        0.0,
        0.0,
    )

    first_joint = Node(
        1000.0,
        0.0,
        0.0,
    )

    second_joint = Node(
        1000.0,
        1000.0,
        0.0,
    )

    end = Node(
        2000.0,
        1000.0,
        0.0,
    )

    tube = build_multi_joint_bent_tube(
        nodes=(
            start,
            first_joint,
            second_joint,
            end,
        ),
        centerline_radii_mm=(
            100.0,
            100.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    assert tube.bend_count == 2

    assert tuple(
        bend.angle_degrees
        for bend in tube.bends
    ) == pytest.approx(
        (
            90.0,
            90.0,
        )
    )


def test_two_90_degree_corners_calculate_tangent_run_lengths():
    """
    A 90-degree bend with 100 mm CLR has a 100 mm tangent setback.

    First segment:
        1000 - 100 = 900

    Middle segment:
        1000 - 100 - 100 = 800

    Final segment:
        1000 - 100 = 900
    """

    tube = build_multi_joint_bent_tube(
        nodes=(
            Node(
                0.0,
                0.0,
                0.0,
            ),
            Node(
                1000.0,
                0.0,
                0.0,
            ),
            Node(
                1000.0,
                1000.0,
                0.0,
            ),
            Node(
                2000.0,
                1000.0,
                0.0,
            ),
        ),
        centerline_radii_mm=(
            100.0,
            100.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    assert tuple(
        run.length_mm
        for run in tube.straight_runs
    ) == pytest.approx(
        (
            900.0,
            800.0,
            900.0,
        )
    )


def test_different_bend_radii_change_middle_run_from_both_ends():
    """
    The middle design segment is shortened independently by
    each adjacent bend's tangent setback.
    """

    tube = build_multi_joint_bent_tube(
        nodes=(
            Node(
                0.0,
                0.0,
                0.0,
            ),
            Node(
                1000.0,
                0.0,
                0.0,
            ),
            Node(
                1000.0,
                1000.0,
                0.0,
            ),
            Node(
                2000.0,
                1000.0,
                0.0,
            ),
        ),
        centerline_radii_mm=(
            100.0,
            200.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    assert tuple(
        run.length_mm
        for run in tube.straight_runs
    ) == pytest.approx(
        (
            900.0,
            700.0,
            800.0,
        )
    )


def test_multi_joint_bend_requires_radius_for_each_joint():
    with pytest.raises(
        ValueError,
        match="radius",
    ):
        build_multi_joint_bent_tube(
            nodes=(
                Node(
                    0.0,
                    0.0,
                    0.0,
                ),
                Node(
                    1000.0,
                    0.0,
                    0.0,
                ),
                Node(
                    1000.0,
                    1000.0,
                    0.0,
                ),
                Node(
                    2000.0,
                    1000.0,
                    0.0,
                ),
            ),
            centerline_radii_mm=(
                100.0,
            ),
            profile=_profile(),
            material=_material(),
        )


def test_middle_design_segment_must_fit_both_bend_setbacks():
    with pytest.raises(
        ValueError,
        match="too short",
    ):
        build_multi_joint_bent_tube(
            nodes=(
                Node(
                    0.0,
                    0.0,
                    0.0,
                ),
                Node(
                    1000.0,
                    0.0,
                    0.0,
                ),
                Node(
                    1000.0,
                    150.0,
                    0.0,
                ),
                Node(
                    2000.0,
                    150.0,
                    0.0,
                ),
            ),
            centerline_radii_mm=(
                100.0,
                100.0,
            ),
            profile=_profile(),
            material=_material(),
        )


def test_reversing_planar_turn_clocks_second_bend_180_degrees():
    """
    A path that turns one direction and then reverses turn direction
    remains planar, but the second bend plane is opposite the first.
    """

    tube = build_multi_joint_bent_tube(
        nodes=(
            Node(
                0.0,
                0.0,
                0.0,
            ),
            Node(
                1000.0,
                0.0,
                0.0,
            ),
            Node(
                1000.0,
                1000.0,
                0.0,
            ),
            Node(
                2000.0,
                1000.0,
                0.0,
            ),
        ),
        centerline_radii_mm=(
            100.0,
            100.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    assert (
        tube.bends[
            0
        ].rotation_degrees
        == pytest.approx(
            0.0
        )
    )

    assert abs(
        tube.bends[
            1
        ].rotation_degrees
    ) == pytest.approx(
        180.0
    )


def test_three_dimensional_second_bend_calculates_plane_rotation():
    """
    Moving the final leg out of the first bend plane must clock the
    second bend plane around the incoming tube direction.
    """

    tube = build_multi_joint_bent_tube(
        nodes=(
            Node(
                0.0,
                0.0,
                0.0,
            ),
            Node(
                1000.0,
                0.0,
                0.0,
            ),
            Node(
                1000.0,
                1000.0,
                0.0,
            ),
            Node(
                1000.0,
                1000.0,
                1000.0,
            ),
        ),
        centerline_radii_mm=(
            100.0,
            100.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    assert abs(
        tube.bends[
            1
        ].rotation_degrees
    ) == pytest.approx(
        90.0
    )
    