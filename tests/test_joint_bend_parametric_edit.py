"""Tests for parametric editing of joint-derived bends."""

import pytest

from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services.joint_bend import (
    bend_specification_from_joint,
)


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def make_material():
    return Material(
        name="DOM Steel",
        density=7850.0,
        yield_strength=350.0,
    )


def make_right_angle_joint():
    profile = make_profile()
    material = make_material()

    outer_start = Node(
        0.0,
        0.0,
        0.0,
    )

    joint_node = Node(
        1000.0,
        0.0,
        0.0,
    )

    outer_end = Node(
        1000.0,
        1000.0,
        0.0,
    )

    first = Member(
        start=outer_start,
        end=joint_node,
        profile=profile,
        material=material,
    )

    second = Member(
        start=joint_node,
        end=outer_end,
        profile=profile,
        material=material,
    )

    joint = Joint(
        node=joint_node,
        members=[
            first,
            second,
        ],
    )

    return (
        joint,
        outer_start,
        joint_node,
        outer_end,
    )


def test_changing_joint_bend_radius_preserves_outer_endpoints():
    (
        joint,
        outer_start,
        joint_node,
        outer_end,
    ) = make_right_angle_joint()

    original = bend_specification_from_joint(
        joint,
        centerline_radius_mm=100.0,
    )

    edited = bend_specification_from_joint(
        joint,
        centerline_radius_mm=200.0,
    )

    assert edited.start_node == outer_start
    assert edited.end_node == outer_end

    assert edited.joint.node == joint_node

    assert original.start_node == edited.start_node
    assert original.end_node == edited.end_node


def test_changing_joint_bend_radius_changes_tangent_setback():
    (
        joint,
        _,
        _,
        _,
    ) = make_right_angle_joint()

    original = bend_specification_from_joint(
        joint,
        centerline_radius_mm=100.0,
    )

    edited = bend_specification_from_joint(
        joint,
        centerline_radius_mm=200.0,
    )

    assert original.tangent_setback_mm == pytest.approx(
        100.0
    )

    assert edited.tangent_setback_mm == pytest.approx(
        200.0
    )


def test_changing_joint_bend_radius_recalculates_run_lengths():
    (
        joint,
        _,
        _,
        _,
    ) = make_right_angle_joint()

    original = bend_specification_from_joint(
        joint,
        centerline_radius_mm=100.0,
    )

    edited = bend_specification_from_joint(
        joint,
        centerline_radius_mm=200.0,
    )

    assert original.tube.straight_runs[
        0
    ].length_mm == pytest.approx(
        900.0
    )

    assert original.tube.straight_runs[
        1
    ].length_mm == pytest.approx(
        900.0
    )

    assert edited.tube.straight_runs[
        0
    ].length_mm == pytest.approx(
        800.0
    )

    assert edited.tube.straight_runs[
        1
    ].length_mm == pytest.approx(
        800.0
    )


def test_joint_bend_radius_cannot_exceed_available_leg_length():
    (
        joint,
        _,
        _,
        _,
    ) = make_right_angle_joint()

    with pytest.raises(
        ValueError,
        match="too short",
    ):
        bend_specification_from_joint(
            joint,
            centerline_radius_mm=1000.0,
        )


def test_joint_bend_angle_remains_fixed_when_radius_changes():
    (
        joint,
        _,
        _,
        _,
    ) = make_right_angle_joint()

    original = bend_specification_from_joint(
        joint,
        centerline_radius_mm=100.0,
    )

    edited = bend_specification_from_joint(
        joint,
        centerline_radius_mm=250.0,
    )

    assert original.bend_angle_degrees == pytest.approx(
        90.0
    )

    assert edited.bend_angle_degrees == pytest.approx(
        90.0
    )
    