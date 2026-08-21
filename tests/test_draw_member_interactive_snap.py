"""Tests for interactive ForgeCAD member centerline snapping."""

import sys
import types


class FakeVector:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


freecad = types.ModuleType("FreeCAD")
freecad.Vector = FakeVector
freecad.ActiveDocument = None
sys.modules["FreeCAD"] = freecad

freecad_gui = types.ModuleType("FreeCADGui")
freecad_gui.addCommand = lambda *args, **kwargs: None
sys.modules["FreeCADGui"] = freecad_gui

part = types.ModuleType("Part")
sys.modules["Part"] = part

qtgui = types.SimpleNamespace(
    QDialog=type("QDialog", (), {}),
    QLineEdit=type("QLineEdit", (), {}),
    QLabel=type("QLabel", (), {}),
    QDoubleValidator=type("QDoubleValidator", (), {}),
    QMessageBox=types.SimpleNamespace(
        warning=lambda *args, **kwargs: None,
    ),
)
qtcore = types.SimpleNamespace(
    Qt=types.SimpleNamespace(
        Key_Escape=27,
    )
)
pyside = types.ModuleType("PySide")
pyside.QtGui = qtgui
pyside.QtCore = qtcore
sys.modules["PySide"] = pyside

from forgecad.geometry import Point3D
from forgecad.adapters.freecad.commands.draw_member_interactive import (
    InteractiveMemberTool,
)


class FakeNode:
    def __init__(self, node_id, point):
        self.NodeID = node_id
        self.Position = FakeVector(
            point.x,
            point.y,
            point.z,
        )


def make_tool():
    tool = InteractiveMemberTool()
    tool.start_point = Point3D(
        0.0,
        100.0,
        0.0,
    )
    return tool


def test_node_snap_has_priority_over_centerline():
    tool = make_tool()

    node = FakeNode(
        "N001",
        Point3D(
            50.0,
            0.0,
            0.0,
        ),
    )

    tool.find_node_snap = lambda position: node
    tool.find_line_snap_point = lambda position: Point3D(
        60.0,
        0.0,
        0.0,
    )

    point, snap_type, angle = tool.resolved_point(
        (100, 100)
    )

    assert snap_type == "NODE"
    assert point == Point3D(
        50.0,
        0.0,
        0.0,
    )
    assert angle is None


def test_centerline_snap_precedes_endpoint_and_free_point():
    tool = make_tool()

    centerline_point = Point3D(
        215.6306,
        0.0453518,
        0.0,
    )

    tool.find_node_snap = lambda position: None
    tool.find_line_snap_point = lambda position: centerline_point
    tool.find_snap_point = lambda position: Point3D(
        999.0,
        999.0,
        0.0,
    )
    tool.screen_to_point = lambda position: Point3D(
        215.6306,
        -0.7970327,
        0.0,
    )

    point, snap_type, angle = tool.resolved_point(
        (100, 100)
    )

    assert snap_type == "LINE"
    assert point == centerline_point
    assert angle is None


def test_centerline_snap_uses_exact_projected_point():
    tool = make_tool()

    exact_point = Point3D(
        215.63059997558594,
        0.04535181447863579,
        0.0,
    )

    tool.find_node_snap = lambda position: None
    tool.find_line_snap_point = lambda position: exact_point

    point, snap_type, _ = tool.resolved_point(
        (100, 100)
    )

    assert snap_type == "LINE"
    assert point.x == exact_point.x
    assert point.y == exact_point.y
    assert point.z == exact_point.z


def test_endpoint_used_when_no_node_or_centerline_snap():
    tool = make_tool()

    endpoint = Point3D(
        500.0,
        0.0,
        0.0,
    )

    tool.find_node_snap = lambda position: None
    tool.find_line_snap_point = lambda position: None
    tool.find_snap_point = lambda position: endpoint

    point, snap_type, angle = tool.resolved_point(
        (100, 100)
    )

    assert snap_type == "ENDPOINT"
    assert point == endpoint
    assert angle is None
