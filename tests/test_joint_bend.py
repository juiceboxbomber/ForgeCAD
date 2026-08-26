"""Tests for converting simple straight joints into bent tubes."""

from math import (
    cos,
    radians,
    sin,
    tan,
)

import pytest

from forgecad.fabrication import (
    Joint,
    Member,
    Node,
)
from forgecad.geometry import (
    Point3D,
)
from forgecad.services import (
    create_default_material,
    create_default_tube_library,
)
from forgecad.services.bent_tube_path import (
    build_bent_tube_centerline,
)
from forgecad.services.joint_bend import (
    bend_specification_from_joint,
)


def default_profile():
    """Return the active default tube profile."""

    return (
        create_default_tube_library()
        .active_profile
    )


def member(
    start,
    end,
):
    """Create one default straight fabrication member."""

    return Member(
        start=start,
        end=end,
        profile=default_profile(),
        material=create_default_material(),
    )


def assert_point_close(
    point,
    expected,
    tolerance=1e-6,
):
    """Assert a Point3D-like value is close to expected XYZ."""

    assert float(point.x) == pytest.approx(
        expected[0],
        abs=tolerance,
    )
    assert float(point.y) == pytest.approx(
        expected[1],
        abs=tolerance,
    )
    assert float(point.z) == pytest.approx(
        expected[2],
        abs=tolerance,
    )


def test_90_degree_joint_creates_expected_tangent_bend():
    joint_node = Node(
        0.0,
        0.0,
        0.0,
    )

    first_outer = Node(
        -1000.0,
        0.0,
        0.0,
    )

    second_outer = Node(
        0.0,
        1000.0,
        0.0,
    )

    first = member(
        first_outer,
        joint_node,
    )

    second = member(
        joint_node,
        second_outer,
    )

    joint = Joint(
        node=joint_node,
        members=[
            first,
            second,
        ],
    )

    result = bend_specification_from_joint(
        joint,
        centerline_radius_mm=100.0,
    )

    assert result.bend_angle_degrees == pytest.approx(
        90.0
    )

    assert result.tangent_setback_mm == pytest.approx(
        100.0
    )

    assert result.tube.straight_runs[
        0
    ].length_mm == pytest.approx(
        900.0
    )

    assert result.tube.straight_runs[
        1
    ].length_mm == pytest.approx(
        900.0
    )

    assert_point_close(
        result.start_tangent,
        (
            -100.0,
            0.0,
            0.0,
        ),
    )

    assert_point_close(
        result.end_tangent,
        (
            0.0,
            100.0,
            0.0,
        ),
    )

    centerline = build_bent_tube_centerline(
        result.tube,
        start_point=Point3D(
            first_outer.x,
            first_outer.y,
            first_outer.z,
        ),
        initial_direction=(
            result.initial_direction
        ),
        initial_bend_normal=(
            result.bend_normal
        ),
    )

    assert_point_close(
        centerline.end_point,
        (
            second_outer.x,
            second_outer.y,
            second_outer.z,
        ),
    )


def test_45_degree_deflection_uses_correct_setback():
    joint_node = Node(
        0.0,
        0.0,
        0.0,
    )

    first_outer = Node(
        -1000.0,
        0.0,
        0.0,
    )

    leg_angle = radians(
        45.0
    )

    second_outer = Node(
        1000.0 * cos(
            leg_angle
        ),
        1000.0 * sin(
            leg_angle
        ),
        0.0,
    )

    first = member(
        first_outer,
        joint_node,
    )

    second = member(
        joint_node,
        second_outer,
    )

    joint = Joint(
        node=joint_node,
        members=[
            first,
            second,
        ],
    )

    result = bend_specification_from_joint(
        joint,
        centerline_radius_mm=100.0,
    )

    expected_setback = (
        100.0
        * tan(
            radians(
                22.5
            )
        )
    )

    assert result.bend_angle_degrees == pytest.approx(
        45.0
    )

    assert result.tangent_setback_mm == pytest.approx(
        expected_setback
    )

    centerline = build_bent_tube_centerline(
        result.tube,
        start_point=Point3D(
            first_outer.x,
            first_outer.y,
            first_outer.z,
        ),
        initial_direction=(
            result.initial_direction
        ),
        initial_bend_normal=(
            result.bend_normal
        ),
    )

    assert_point_close(
        centerline.end_point,
        (
            second_outer.x,
            second_outer.y,
            second_outer.z,
        ),
    )


def test_collinear_members_are_rejected():
    joint_node = Node(
        0.0,
        0.0,
        0.0,
    )

    first = member(
        Node(
            -1000.0,
            0.0,
            0.0,
        ),
        joint_node,
    )

    second = member(
        joint_node,
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            first,
            second,
        ],
    )

    with pytest.raises(
        ValueError,
        match="collinear",
    ):
        bend_specification_from_joint(
            joint,
            centerline_radius_mm=100.0,
        )


def test_requested_radius_must_fit_both_straight_legs():
    joint_node = Node(
        0.0,
        0.0,
        0.0,
    )

    first = member(
        Node(
            -400.0,
            0.0,
            0.0,
        ),
        joint_node,
    )

    second = member(
        joint_node,
        Node(
            0.0,
            1000.0,
            0.0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            first,
            second,
        ],
    )

    with pytest.raises(
        ValueError,
        match="too short",
    ):
        bend_specification_from_joint(
            joint,
            centerline_radius_mm=500.0,
        )
