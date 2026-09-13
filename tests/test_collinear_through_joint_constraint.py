"""Tests for collinear through-joint constraints."""

from dataclasses import dataclass

from forgecad.fabrication import Joint
from forgecad.fabrication.node import Node
from forgecad.geometry.point import Point3D
from forgecad.services.joint_constraints import (
    CollinearThroughConstraint,
    collinear_through_constraint_for_joint,
    members_are_collinear_through_joint,
    solve_collinear_through_joint,
)


@dataclass(
    frozen=True,
)
class FakeMember:
    """Minimal member shape needed by the constraint solver."""

    start: Node
    end: Node


def test_straight_through_members_are_collinear():
    joint = Node(
        0.0,
        0.0,
        0.0,
    )

    left = FakeMember(
        start=Node(
            -1000.0,
            0.0,
            0.0,
        ),
        end=joint,
    )

    right = FakeMember(
        start=joint,
        end=Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    assert members_are_collinear_through_joint(
        left,
        right,
        joint,
    )


def test_angled_members_are_not_collinear():
    joint = Node(
        0.0,
        0.0,
        0.0,
    )

    left = FakeMember(
        start=Node(
            -1000.0,
            0.0,
            0.0,
        ),
        end=joint,
    )

    right = FakeMember(
        start=joint,
        end=Node(
            1000.0,
            250.0,
            0.0,
        ),
    )

    assert not members_are_collinear_through_joint(
        left,
        right,
        joint,
    )


def test_member_not_connected_to_joint_is_rejected():
    joint = Node(
        0.0,
        0.0,
        0.0,
    )

    first = FakeMember(
        start=Node(
            -1000.0,
            0.0,
            0.0,
        ),
        end=joint,
    )

    second = FakeMember(
        start=Node(
            500.0,
            500.0,
            0.0,
        ),
        end=Node(
            1000.0,
            500.0,
            0.0,
        ),
    )

    assert not members_are_collinear_through_joint(
        first,
        second,
        joint,
    )


def test_off_axis_drag_projects_back_to_through_axis():
    constraint = CollinearThroughConstraint(
        axis_start=Point3D(
            -1000.0,
            0.0,
            0.0,
        ),
        axis_end=Point3D(
            1000.0,
            0.0,
            0.0,
        ),
    )

    solved = solve_collinear_through_joint(
        proposed_position=Point3D(
            250.0,
            150.0,
            0.0,
        ),
        constraint=constraint,
    )

    assert solved == Point3D(
        250.0,
        0.0,
        0.0,
    )


def test_projection_works_on_3d_axis():
    constraint = CollinearThroughConstraint(
        axis_start=Point3D(
            0.0,
            0.0,
            0.0,
        ),
        axis_end=Point3D(
            1000.0,
            1000.0,
            1000.0,
        ),
    )

    solved = solve_collinear_through_joint(
        proposed_position=Point3D(
            500.0,
            500.0,
            800.0,
        ),
        constraint=constraint,
    )

    assert solved == Point3D(
        600.0,
        600.0,
        600.0,
    )


def test_constraint_is_derived_from_identified_through_pair():
    joint_node = Node(
        0.0,
        0.0,
        0.0,
    )

    left = FakeMember(
        start=Node(
            -1000.0,
            0.0,
            0.0,
        ),
        end=joint_node,
    )

    right = FakeMember(
        start=joint_node,
        end=Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    branch = FakeMember(
        start=joint_node,
        end=Node(
            0.0,
            500.0,
            0.0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=(
            left,
            right,
            branch,
        ),
    )

    constraint = (
        collinear_through_constraint_for_joint(
            joint
        )
    )

    assert constraint is not None

    assert constraint.axis_start == Point3D(
        -1000.0,
        0.0,
        0.0,
    )

    assert constraint.axis_end == Point3D(
        1000.0,
        0.0,
        0.0,
    )

def test_constraint_is_derived_from_continuous_through_member():
    joint_node = Node(
        0.0,
        0.0,
        0.0,
    )

    through = FakeMember(
        start=Node(
            -1000.0,
            0.0,
            0.0,
        ),
        end=Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    branch = FakeMember(
        start=joint_node,
        end=Node(
            0.0,
            500.0,
            0.0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=(
            through,
            branch,
        ),
    )

    constraint = (
        collinear_through_constraint_for_joint(
            joint
        )
    )

    assert constraint is not None

    assert constraint.axis_start == Point3D(
        -1000.0,
        0.0,
        0.0,
    )

    assert constraint.axis_end == Point3D(
        1000.0,
        0.0,
        0.0,
    )
