"""Tests for ForgeCAD 3D vector operations used by bent-tube geometry."""

import pytest

from forgecad.geometry import (
    Vector3D,
)


def test_cross_product_uses_right_hand_rule():
    x_axis = Vector3D(
        1.0,
        0.0,
        0.0,
    )
    y_axis = Vector3D(
        0.0,
        1.0,
        0.0,
    )

    result = x_axis.cross(
        y_axis
    )

    assert result == Vector3D(
        0.0,
        0.0,
        1.0,
    )


def test_vector_rotates_about_axis():
    vector = Vector3D(
        1.0,
        0.0,
        0.0,
    )

    result = vector.rotated_about(
        Vector3D(
            0.0,
            0.0,
            1.0,
        ),
        90.0,
    )

    assert result.x == pytest.approx(
        0.0,
        abs=1e-9,
    )
    assert result.y == pytest.approx(
        1.0,
    )
    assert result.z == pytest.approx(
        0.0,
        abs=1e-9,
    )
