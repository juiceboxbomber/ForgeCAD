"""Tests for ForgeCAD tube-bend domain geometry."""

import math

import pytest

from forgecad.fabrication import (
    Bend,
)


def test_bend_stores_geometry():
    bend = Bend(
        angle_degrees=90.0,
        centerline_radius=152.4,
        rotation_degrees=45.0,
    )

    assert bend.angle_degrees == 90.0
    assert bend.centerline_radius == 152.4
    assert bend.rotation_degrees == 45.0


def test_bend_arc_length_is_centerline_developed_length():
    bend = Bend(
        angle_degrees=90.0,
        centerline_radius=100.0,
    )

    assert bend.arc_length == pytest.approx(
        math.pi * 50.0
    )


def test_bend_tangent_setback():
    bend = Bend(
        angle_degrees=90.0,
        centerline_radius=100.0,
    )

    assert bend.tangent_setback == pytest.approx(
        100.0
    )


def test_bend_rotation_is_normalized():
    bend = Bend(
        angle_degrees=45.0,
        centerline_radius=100.0,
        rotation_degrees=450.0,
    )

    assert bend.rotation_degrees == pytest.approx(
        90.0
    )


@pytest.mark.parametrize(
    "angle",
    (
        0.0,
        -45.0,
        180.0,
        200.0,
    ),
)
def test_bend_rejects_invalid_angle(
    angle,
):
    with pytest.raises(
        ValueError,
        match="Bend angle",
    ):
        Bend(
            angle_degrees=angle,
            centerline_radius=100.0,
        )


def test_bend_rejects_nonpositive_radius():
    with pytest.raises(
        ValueError,
        match="centerline radius",
    ):
        Bend(
            angle_degrees=90.0,
            centerline_radius=0.0,
        )
