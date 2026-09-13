"""Tests for Split Member perpendicular preview geometry."""

import sys
import types
from types import SimpleNamespace

import pytest


class FakeQDialog:
    pass


class FakeQMessageBox:
    @staticmethod
    def warning(
        *args,
        **kwargs,
    ):
        return None


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.ActiveDocument = None
fake_freecad.Vector = (
    lambda x, y, z: SimpleNamespace(
        x=x,
        y=y,
        z=z,
    )
)

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)
fake_freecad_gui.Selection = SimpleNamespace(
    getSelection=lambda: [],
    clearSelection=lambda: None,
    addSelection=lambda obj: None,
)
fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)

fake_part = types.ModuleType(
    "Part"
)
fake_part.makeLine = (
    lambda start, end: SimpleNamespace(
        start=start,
        end=end,
    )
)

fake_pyside = types.ModuleType(
    "PySide"
)
fake_pyside.QtGui = SimpleNamespace(
    QDialog=FakeQDialog,
    QMessageBox=FakeQMessageBox,
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


from forgecad.geometry import (
    Point3D,
)
from forgecad.adapters.freecad.commands import (
    split_member as module,
)


def test_xy_member_preview_is_perpendicular():
    start = Point3D(
        0.0,
        0.0,
        0.0,
    )

    end = Point3D(
        1000.0,
        0.0,
        0.0,
    )

    ux, uy, uz = (
        module.perpendicular_unit_vector(
            start,
            end,
        )
    )

    assert ux == pytest.approx(
        0.0
    )

    assert abs(
        uy
    ) == pytest.approx(
        1.0
    )

    assert uz == pytest.approx(
        0.0
    )


def test_diagonal_xy_preview_is_perpendicular():
    start = Point3D(
        0.0,
        0.0,
        0.0,
    )

    end = Point3D(
        1000.0,
        500.0,
        0.0,
    )

    ux, uy, uz = (
        module.perpendicular_unit_vector(
            start,
            end,
        )
    )

    dx = (
        end.x
        - start.x
    )

    dy = (
        end.y
        - start.y
    )

    dz = (
        end.z
        - start.z
    )

    dot = (
        dx * ux
        + dy * uy
        + dz * uz
    )

    assert dot == pytest.approx(
        0.0
    )


def test_vertical_member_preview_has_horizontal_perpendicular():
    result = (
        module.perpendicular_unit_vector(
            Point3D(
                0.0,
                0.0,
                0.0,
            ),
            Point3D(
                0.0,
                0.0,
                1000.0,
            ),
        )
    )

    assert result == (
        1.0,
        0.0,
        0.0,
    )


def test_preview_line_extends_equal_distance_each_side():
    center = Point3D(
        500.0,
        0.0,
        0.0,
    )

    first, second = (
        module.preview_line_endpoints(
            center,
            Point3D(
                0.0,
                0.0,
                0.0,
            ),
            Point3D(
                1000.0,
                0.0,
                0.0,
            ),
            30.0,
        )
    )

    assert first.x == pytest.approx(
        500.0
    )

    assert second.x == pytest.approx(
        500.0
    )

    assert abs(
        first.y
    ) == pytest.approx(
        30.0
    )

    assert abs(
        second.y
    ) == pytest.approx(
        30.0
    )

    assert first.y == pytest.approx(
        -second.y
    )
