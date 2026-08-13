"""Tests for ForgeCAD workspace calculations."""

import sys
import types

import pytest


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.Vector = FakeVector

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_part = types.ModuleType(
    "Part"
)
fake_part.makeLine = (
    lambda start, end: (
        "line",
        start,
        end,
    )
)
fake_part.makeCompound = (
    lambda shapes: (
        "compound",
        tuple(
            shapes
        ),
    )
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "FreeCADGui"
] = fake_freecad_gui
sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad.workspace import (
    _grid_positions,
    build_workspace_axes_shape,
    build_workspace_grid_shape,
    workspace_bounds,
)


def test_workspace_bounds_are_centered_on_origin():
    assert workspace_bounds(
        4000.0,
        2000.0,
    ) == (
        -2000.0,
        2000.0,
        -1000.0,
        1000.0,
    )


def test_grid_positions_include_workspace_edges():
    assert _grid_positions(
        -200.0,
        200.0,
        100.0,
    ) == (
        -200.0,
        -100.0,
        0.0,
        100.0,
        200.0,
    )


def test_grid_positions_reject_nonpositive_spacing():
    with pytest.raises(
        ValueError,
        match="Grid spacing",
    ):
        _grid_positions(
            -100.0,
            100.0,
            0.0,
        )


def test_grid_shape_contains_boundary_and_major_grid():
    shape = build_workspace_grid_shape(
        width_mm=400.0,
        height_mm=200.0,
        major_grid_mm=100.0,
    )

    assert shape[
        0
    ] == "compound"

    # 4 boundary edges
    # + 4 non-origin vertical major lines
    # + 2 non-origin horizontal major lines
    assert len(
        shape[
            1
        ]
    ) == 10


def test_axes_shape_contains_x_and_y_axes():
    shape = build_workspace_axes_shape(
        width_mm=400.0,
        height_mm=200.0,
    )

    assert shape[
        0
    ] == "compound"
    assert len(
        shape[
            1
        ]
    ) == 2
