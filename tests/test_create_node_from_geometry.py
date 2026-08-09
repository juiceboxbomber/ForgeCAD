"""Tests for ForgeCAD geometry-node command helpers."""

import sys
import types


# ---------------------------------------------------------
# FreeCAD stubs
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)

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
    "forgecad.adapters.freecad.commands.create_node_from_geometry",
    None,
)

from forgecad.adapters.freecad.commands.create_node_from_geometry import (
    selected_vertex_points,
)


# ---------------------------------------------------------
# Fake FreeCAD selection geometry
# ---------------------------------------------------------

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


class FakeVertex:
    ShapeType = "Vertex"

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.Point = FakeVector(
            x,
            y,
            z,
        )


class FakeEdge:
    ShapeType = "Edge"


class FakeFace:
    ShapeType = "Face"


class FakeSelectionEx:
    def __init__(
        self,
        subobjects,
    ):
        self.SubObjects = list(
            subobjects
        )


# ---------------------------------------------------------
# Vertex extraction
# ---------------------------------------------------------

def test_selected_vertex_points_returns_one_vertex():
    vertex = FakeVertex(
        100,
        200,
        300,
    )

    result = selected_vertex_points(
        [
            FakeSelectionEx(
                [vertex]
            )
        ]
    )

    assert result == [
        vertex.Point
    ]


def test_selected_vertex_points_returns_multiple_vertices():
    vertex_1 = FakeVertex(
        0,
        0,
        0,
    )

    vertex_2 = FakeVertex(
        100,
        200,
        300,
    )

    result = selected_vertex_points(
        [
            FakeSelectionEx(
                [
                    vertex_1,
                    vertex_2,
                ]
            )
        ]
    )

    assert result == [
        vertex_1.Point,
        vertex_2.Point,
    ]


def test_selected_vertex_points_supports_multiple_selection_entries():
    vertex_1 = FakeVertex(
        10,
        20,
        30,
    )

    vertex_2 = FakeVertex(
        40,
        50,
        60,
    )

    result = selected_vertex_points(
        [
            FakeSelectionEx(
                [vertex_1]
            ),
            FakeSelectionEx(
                [vertex_2]
            ),
        ]
    )

    assert result == [
        vertex_1.Point,
        vertex_2.Point,
    ]


def test_selected_vertex_points_ignores_edges():
    result = selected_vertex_points(
        [
            FakeSelectionEx(
                [
                    FakeEdge(),
                ]
            )
        ]
    )

    assert result == []


def test_selected_vertex_points_ignores_faces():
    result = selected_vertex_points(
        [
            FakeSelectionEx(
                [
                    FakeFace(),
                ]
            )
        ]
    )

    assert result == []


def test_selected_vertex_points_ignores_non_vertex_objects():
    vertex = FakeVertex(
        1,
        2,
        3,
    )

    result = selected_vertex_points(
        [
            FakeSelectionEx(
                [
                    FakeEdge(),
                    vertex,
                    FakeFace(),
                ]
            )
        ]
    )

    assert result == [
        vertex.Point
    ]


def test_selected_vertex_points_empty_selection_returns_empty():
    assert (
        selected_vertex_points(
            []
        )
        == []
    )


def test_selected_vertex_points_ignores_vertex_without_point():
    class FakeBrokenVertex:
        ShapeType = "Vertex"

    result = selected_vertex_points(
        [
            FakeSelectionEx(
                [
                    FakeBrokenVertex(),
                ]
            )
        ]
    )

    assert result == []
    