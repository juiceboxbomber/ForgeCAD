"""Tests for ForgeCAD joint marker visualization."""

import sys
import types


class FakeVector:
    """Minimal FreeCAD vector."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(
            x
        )

        self.y = float(
            y
        )

        self.z = float(
            z
        )


class FakeSphere:
    """Minimal Part sphere marker."""

    def __init__(
        self,
        radius,
        center,
    ):
        self.radius = float(
            radius
        )

        self.center = center


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.Vector = (
    FakeVector
)

fake_part = types.ModuleType(
    "Part"
)

fake_part.makeSphere = (
    lambda radius, center: FakeSphere(
        radius,
        center,
    )
)


sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = types.ModuleType(
    "FreeCADGui"
)

sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad import (
    joint_status_objects,
)


# Patch the already-imported adapter directly so this test
# remains independent of pytest collection/import order.
joint_status_objects.FreeCAD = (
    fake_freecad
)

joint_status_objects.Part = (
    fake_part
)


def test_attention_marker_is_largest():
    assert (
        joint_status_objects
        .marker_radius_for_category(
            "attention"
        )
        == 14.0
    )


def test_manual_marker_is_medium():
    assert (
        joint_status_objects
        .marker_radius_for_category(
            "manual"
        )
        == 11.0
    )


def test_automatic_marker_is_smallest():
    assert (
        joint_status_objects
        .marker_radius_for_category(
            "automatic"
        )
        == 9.0
    )


def test_unknown_category_uses_default_radius():
    assert (
        joint_status_objects
        .marker_radius_for_category(
            "unknown"
        )
        == 9.0
    )


def test_marker_shape_uses_joint_position():
    position = FakeVector(
        10,
        20,
        30,
    )

    shape = (
        joint_status_objects
        .build_joint_marker_shape(
            position,
            6.0,
        )
    )

    assert (
        shape.radius
        == 6.0
    )

    assert (
        shape.center.x
        == 10
    )

    assert (
        shape.center.y
        == 20
    )

    assert (
        shape.center.z
        == 30
    )


def test_marker_rejects_zero_radius():
    position = FakeVector(
        0,
        0,
        0,
    )

    try:
        joint_status_objects.build_joint_marker_shape(
            position,
            0,
        )

    except ValueError as error:
        assert (
            "greater than zero"
            in str(
                error
            )
        )

    else:
        raise AssertionError(
            "Expected zero-radius marker to fail."
        )
    