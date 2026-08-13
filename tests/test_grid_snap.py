"""Tests for ForgeCAD grid snapping."""

import pytest

from forgecad.services.grid_snap import (
    snap_coordinate_to_grid,
    snap_xy_coordinates,
    validate_grid_spacing,
)


def test_grid_spacing_must_be_positive():
    with pytest.raises(
        ValueError,
        match="Grid spacing",
    ):
        validate_grid_spacing(
            0.0
        )


def test_coordinate_snaps_to_nearest_increment():
    assert (
        snap_coordinate_to_grid(
            61.0,
            25.0,
        )
        == 50.0
    )

    assert (
        snap_coordinate_to_grid(
            64.0,
            25.0,
        )
        == 75.0
    )


def test_negative_coordinate_snaps_around_origin():
    assert (
        snap_coordinate_to_grid(
            -61.0,
            25.0,
        )
        == -50.0
    )

    assert (
        snap_coordinate_to_grid(
            -64.0,
            25.0,
        )
        == -75.0
    )


def test_xy_coordinates_snap_independently():
    assert snap_xy_coordinates(
        62.0,
        113.0,
        25.0,
    ) == (
        50.0,
        125.0,
    )


def test_grid_origin_can_be_offset():
    assert (
        snap_coordinate_to_grid(
            36.0,
            25.0,
            origin=10.0,
        )
        == 35.0
    )
