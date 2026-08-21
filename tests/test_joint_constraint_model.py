"""Tests for first-class ForgeCAD joint constraint models."""

from forgecad.fabrication.joint_constraint import (
    CollinearThroughConstraint,
    JointConstraintKind,
)
from forgecad.geometry.point import Point3D


def test_collinear_through_constraint_has_explicit_kind():
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

    assert (
        constraint.kind
        == JointConstraintKind.COLLINEAR_THROUGH
    )


def test_collinear_through_constraint_preserves_axis():
    start = Point3D(
        -1000.0,
        50.0,
        25.0,
    )

    end = Point3D(
        1000.0,
        50.0,
        25.0,
    )

    constraint = CollinearThroughConstraint(
        axis_start=start,
        axis_end=end,
    )

    assert constraint.axis_start == start
    assert constraint.axis_end == end


def test_joint_constraint_kind_has_stable_persistent_value():
    assert (
        JointConstraintKind.COLLINEAR_THROUGH.value
        == "collinear_through"
    )


def test_collinear_through_constraint_is_immutable():
    constraint = CollinearThroughConstraint(
        axis_start=Point3D(
            0.0,
            0.0,
            0.0,
        ),
        axis_end=Point3D(
            1000.0,
            0.0,
            0.0,
        ),
    )

    try:
        constraint.axis_start = Point3D(
            10.0,
            0.0,
            0.0,
        )
    except (
        AttributeError,
        TypeError,
    ):
        pass
    else:
        raise AssertionError(
            "Joint constraints must be immutable."
        )
