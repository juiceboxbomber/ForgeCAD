"""Tests for ForgeCAD reference-plane geometry."""

import pytest

from forgecad.geometry.reference_plane import (
    ReferencePlane,
    ReferencePlaneOrientation,
)


def test_xy_plane_uses_z_offset():
    plane = ReferencePlane(
        name="Roof Plane",
        orientation=ReferencePlaneOrientation.XY,
        offset=1200.0,
    )

    assert plane.name == "Roof Plane"
    assert plane.orientation == ReferencePlaneOrientation.XY

    assert plane.origin.x == pytest.approx(
        0.0
    )
    assert plane.origin.y == pytest.approx(
        0.0
    )
    assert plane.origin.z == pytest.approx(
        1200.0
    )

    assert plane.normal.x == pytest.approx(
        0.0
    )
    assert plane.normal.y == pytest.approx(
        0.0
    )
    assert plane.normal.z == pytest.approx(
        1.0
    )


def test_xz_plane_uses_y_offset():
    plane = ReferencePlane(
        name="Left Rail Plane",
        orientation="XZ",
        offset=350.0,
    )

    assert plane.orientation == ReferencePlaneOrientation.XZ

    assert plane.origin.x == pytest.approx(
        0.0
    )
    assert plane.origin.y == pytest.approx(
        350.0
    )
    assert plane.origin.z == pytest.approx(
        0.0
    )

    assert plane.normal.x == pytest.approx(
        0.0
    )
    assert plane.normal.y == pytest.approx(
        1.0
    )
    assert plane.normal.z == pytest.approx(
        0.0
    )


def test_yz_plane_uses_x_offset():
    plane = ReferencePlane(
        name="Front Hoop Plane",
        orientation="YZ",
        offset=900.0,
    )

    assert plane.orientation == ReferencePlaneOrientation.YZ

    assert plane.origin.x == pytest.approx(
        900.0
    )
    assert plane.origin.y == pytest.approx(
        0.0
    )
    assert plane.origin.z == pytest.approx(
        0.0
    )

    assert plane.normal.x == pytest.approx(
        1.0
    )
    assert plane.normal.y == pytest.approx(
        0.0
    )
    assert plane.normal.z == pytest.approx(
        0.0
    )


def test_name_is_trimmed():
    plane = ReferencePlane(
        name="  Center Plane  ",
        orientation="xz",
    )

    assert plane.name == "Center Plane"
    assert plane.orientation == ReferencePlaneOrientation.XZ


def test_empty_name_is_rejected():
    with pytest.raises(
        ValueError,
        match="requires a name",
    ):
        ReferencePlane(
            name="   ",
            orientation="XY",
        )


def test_invalid_orientation_is_rejected():
    with pytest.raises(
        ValueError,
        match="XY, XZ, or YZ",
    ):
        ReferencePlane(
            name="Bad Plane",
            orientation="AB",
        )


def test_negative_offset_is_allowed():
    plane = ReferencePlane(
        name="Right Rail Plane",
        orientation="XZ",
        offset=-350.0,
    )

    assert plane.offset == pytest.approx(
        -350.0
    )

    assert plane.origin.y == pytest.approx(
        -350.0
    )
    