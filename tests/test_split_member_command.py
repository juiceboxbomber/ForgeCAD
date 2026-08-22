"""Tests for the interactive FreeCAD Split Member command."""

import sys
import types
from types import SimpleNamespace


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
fake_part.makeSphere = (
    lambda radius, center: SimpleNamespace(
        radius=radius,
        center=center,
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


class FakeView:
    def getPointOnScreen(
        self,
        vector,
    ):
        return (
            vector.x,
            vector.y,
        )


def member_object():
    return SimpleNamespace(
        MemberID="M001",
        StartPoint=SimpleNamespace(
            x=0.0,
            y=0.0,
            z=0.0,
        ),
        EndPoint=SimpleNamespace(
            x=1000.0,
            y=0.0,
            z=0.0,
        ),
    )


def test_member_centerline_reads_selected_member():
    start, end = (
        module.member_centerline(
            member_object()
        )
    )

    assert start == Point3D(
        0.0,
        0.0,
        0.0,
    )

    assert end == Point3D(
        1000.0,
        0.0,
        0.0,
    )


def test_screen_point_on_segment_returns_exact_3d_point():
    point, distance, parameter = (
        module.screen_point_on_segment(
            FakeView(),
            (
                250.0,
                10.0,
            ),
            Point3D(
                0.0,
                0.0,
                0.0,
            ),
            Point3D(
                1000.0,
                0.0,
                500.0,
            ),
        )
    )

    assert parameter == 0.25

    assert point == Point3D(
        250.0,
        0.0,
        125.0,
    )

    assert distance == 10.0


def test_screen_projection_clamps_to_member_segment():
    point, distance, parameter = (
        module.screen_point_on_segment(
            FakeView(),
            (
                1200.0,
                0.0,
            ),
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
        )
    )

    assert parameter == 1.0

    assert point == Point3D(
        1000.0,
        0.0,
        0.0,
    )


def test_split_tool_rejects_endpoint_location():
    tool = (
        module.InteractiveSplitMemberTool(
            object(),
            member_object(),
        )
    )

    tool.view = FakeView()

    assert (
        tool.resolve_split_point(
            (
                0.0,
                0.0,
            )
        )
        is None
    )

    assert (
        tool.resolve_split_point(
            (
                1000.0,
                0.0,
            )
        )
        is None
    )


def test_split_tool_accepts_interior_point_within_snap_distance():
    tool = (
        module.InteractiveSplitMemberTool(
            object(),
            member_object(),
        )
    )

    tool.view = FakeView()

    point = (
        tool.resolve_split_point(
            (
                500.0,
                10.0,
            )
        )
    )

    assert point == Point3D(
        500.0,
        0.0,
        0.0,
    )


def test_split_tool_rejects_cursor_far_from_member():
    tool = (
        module.InteractiveSplitMemberTool(
            object(),
            member_object(),
        )
    )

    tool.view = FakeView()

    assert (
        tool.resolve_split_point(
            (
                500.0,
                100.0,
            )
        )
        is None
    )
