"""Tests for ForgeCAD offset-node command helpers."""

import sys
import types

import pytest


# ---------------------------------------------------------
# FreeCAD stub
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)


class FakeVector:
    """Minimal FreeCAD Vector replacement."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


fake_freecad.Vector = FakeVector
fake_freecad.ActiveDocument = None

sys.modules[
    "FreeCAD"
] = fake_freecad


# ---------------------------------------------------------
# Part stub
# ---------------------------------------------------------

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


# ---------------------------------------------------------
# FreeCADGui stub
# ---------------------------------------------------------

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)

fake_freecad_gui.getMainWindow = (
    lambda: None
)

sys.modules[
    "FreeCADGui"
] = fake_freecad_gui


# ---------------------------------------------------------
# PySide stubs
# ---------------------------------------------------------

fake_pyside = types.ModuleType(
    "PySide"
)

fake_qtgui = types.ModuleType(
    "QtGui"
)

fake_qtcore = types.ModuleType(
    "QtCore"
)


class FakeDialog:
    pass


class FakeLineEdit:
    pass


fake_qtgui.QDialog = (
    FakeDialog
)

fake_qtgui.QLineEdit = (
    FakeLineEdit
)

fake_pyside.QtGui = (
    fake_qtgui
)

fake_pyside.QtCore = (
    fake_qtcore
)

sys.modules[
    "PySide"
] = fake_pyside

sys.modules[
    "PySide.QtGui"
] = fake_qtgui

sys.modules[
    "PySide.QtCore"
] = fake_qtcore


# ---------------------------------------------------------
# Import module under test
# ---------------------------------------------------------

sys.modules.pop(
    "forgecad.adapters.freecad.commands.create_offset_node",
    None,
)

from forgecad.adapters.freecad.commands.create_offset_node import (
    is_forgecad_node,
    offset_point,
)


# ---------------------------------------------------------
# Fake ForgeCAD objects
# ---------------------------------------------------------

class FakeNode:
    def __init__(
        self,
        node_id="N001",
        position=(0, 0, 0),
    ):
        self.NodeID = node_id
        self.Position = FakeVector(
            *position
        )


class FakeUnrelatedObject:
    pass


# ---------------------------------------------------------
# Node recognition
# ---------------------------------------------------------

def test_forgecad_node_is_recognized():
    node = FakeNode()

    assert (
        is_forgecad_node(
            node
        )
        is True
    )


def test_none_is_not_forgecad_node():
    assert (
        is_forgecad_node(
            None
        )
        is False
    )


def test_object_without_node_id_is_rejected():
    obj = FakeUnrelatedObject()

    obj.Position = FakeVector(
        0,
        0,
        0,
    )

    assert (
        is_forgecad_node(
            obj
        )
        is False
    )


def test_object_without_position_is_rejected():
    obj = FakeUnrelatedObject()

    obj.NodeID = "N001"

    assert (
        is_forgecad_node(
            obj
        )
        is False
    )


# ---------------------------------------------------------
# Offset calculations
# ---------------------------------------------------------

def test_zero_offset_preserves_position():
    base = FakeVector(
        100,
        200,
        300,
    )

    result = offset_point(
        base,
        0,
        0,
        0,
    )

    assert result.x == pytest.approx(
        100
    )

    assert result.y == pytest.approx(
        200
    )

    assert result.z == pytest.approx(
        300
    )


def test_positive_z_offset():
    base = FakeVector(
        0,
        0,
        0,
    )

    result = offset_point(
        base,
        0,
        0,
        1000,
    )

    assert result.x == pytest.approx(
        0
    )

    assert result.y == pytest.approx(
        0
    )

    assert result.z == pytest.approx(
        1000
    )


def test_xyz_offset():
    base = FakeVector(
        100,
        200,
        300,
    )

    result = offset_point(
        base,
        500,
        250,
        750,
    )

    assert result.x == pytest.approx(
        600
    )

    assert result.y == pytest.approx(
        450
    )

    assert result.z == pytest.approx(
        1050
    )


def test_negative_offsets():
    base = FakeVector(
        1000,
        500,
        250,
    )

    result = offset_point(
        base,
        -200,
        -100,
        -50,
    )

    assert result.x == pytest.approx(
        800
    )

    assert result.y == pytest.approx(
        400
    )

    assert result.z == pytest.approx(
        200
    )


def test_offset_values_are_converted_to_float():
    base = FakeVector(
        10,
        20,
        30,
    )

    result = offset_point(
        base,
        1,
        2,
        3,
    )

    assert isinstance(
        result.x,
        float,
    )

    assert isinstance(
        result.y,
        float,
    )

    assert isinstance(
        result.z,
        float,
    )
    