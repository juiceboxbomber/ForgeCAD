"""Tests for ForgeCAD Create Reference Plane command helpers."""

import sys
import types
from types import SimpleNamespace

import pytest


class FakeQDialog:
    Accepted = 1


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.ActiveDocument = None

fake_freecad.Vector = (
    lambda x, y, z: SimpleNamespace(
        x=float(x),
        y=float(y),
        z=float(z),
    )
)

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_freecad_gui.Selection = SimpleNamespace(
    clearSelection=lambda: None,
    addSelection=lambda obj: None,
)

fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)

fake_part = types.ModuleType(
    "Part"
)

fake_part.makePolygon = (
    lambda points: tuple(
        points
    )
)

fake_part.Face = (
    lambda wire: SimpleNamespace(
        Wire=wire
    )
)

fake_pyside = types.ModuleType(
    "PySide"
)

fake_pyside.QtGui = SimpleNamespace(
    QDialog=FakeQDialog,
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

sys.modules[
    "PySide"
] = fake_pyside


dialog_module = types.ModuleType(
    "forgecad.adapters.freecad.dialogs.create_reference_plane"
)

dialog_module.CreateReferencePlaneDialog = (
    FakeQDialog
)

sys.modules[
    "forgecad.adapters.freecad.dialogs.create_reference_plane"
] = dialog_module


from forgecad.geometry import (
    ReferencePlane,
)
from forgecad.adapters.freecad.commands import (
    create_reference_plane as module,
)


def coordinates(
    shape,
):
    return tuple(
        (
            point.x,
            point.y,
            point.z,
        )
        for point in shape.Wire
    )


def test_xy_plane_shape_uses_z_offset():
    shape = module.plane_shape(
        ReferencePlane(
            name="Roof",
            orientation="XY",
            offset=1200.0,
        ),
        size=100.0,
    )

    points = coordinates(
        shape
    )

    assert all(
        point[
            2
        ] == pytest.approx(
            1200.0
        )
        for point in points
    )


def test_xz_plane_shape_uses_y_offset():
    shape = module.plane_shape(
        ReferencePlane(
            name="Rail",
            orientation="XZ",
            offset=350.0,
        ),
        size=100.0,
    )

    points = coordinates(
        shape
    )

    assert all(
        point[
            1
        ] == pytest.approx(
            350.0
        )
        for point in points
    )


def test_yz_plane_shape_uses_x_offset():
    shape = module.plane_shape(
        ReferencePlane(
            name="Hoop",
            orientation="YZ",
            offset=900.0,
        ),
        size=100.0,
    )

    points = coordinates(
        shape
    )

    assert all(
        point[
            0
        ] == pytest.approx(
            900.0
        )
        for point in points
    )


def test_plane_shape_is_closed():
    shape = module.plane_shape(
        ReferencePlane(
            name="Center",
            orientation="XZ",
            offset=0.0,
        ),
        size=100.0,
    )

    points = coordinates(
        shape
    )

    assert points[
        0
    ] == points[
        -1
    ]

    assert len(
        points
    ) == 5


def test_non_positive_display_size_is_rejected():
    plane = ReferencePlane(
        name="Center",
        orientation="XZ",
        offset=0.0,
    )

    with pytest.raises(
        ValueError,
        match="display size must be positive",
    ):
        module.plane_shape(
            plane,
            size=0.0,
        )
