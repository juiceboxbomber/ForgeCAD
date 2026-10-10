"""Tests for the interactive FreeCAD Split Member command."""

import sys
import types

import pytest
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


from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
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


def bent_member_object():
    profile = TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )
    material = Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )
    tube = BentTube(
        straight_runs=(
            StraightRun(500.0),
            StraightRun(750.0),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
        ),
        profile=profile,
        material=material,
    )

    proxy = SimpleNamespace(
        _tube_from_properties=lambda obj: tube,
    )

    return SimpleNamespace(
        Proxy=proxy,
        StartPoint=SimpleNamespace(
            x=0.0,
            y=0.0,
            z=0.0,
        ),
        InitialDirection=SimpleNamespace(
            x=1.0,
            y=0.0,
            z=0.0,
        ),
        InitialBendNormal=SimpleNamespace(
            x=0.0,
            y=0.0,
            z=1.0,
        ),
        TubeProfile="1.75 x 0.120",
        BendCount=1,
    )


def test_split_command_recognizes_bent_member():
    assert module.is_forgecad_member(
        bent_member_object()
    )


def test_bent_member_centerline_segments_use_physical_straight_runs():
    segments = module.member_centerline_segments(
        bent_member_object()
    )

    assert len(segments) == 2

    first_start, first_end = segments[0]
    second_start, second_end = segments[1]

    assert first_start == Point3D(
        0.0,
        0.0,
        0.0,
    )
    assert first_end == Point3D(
        500.0,
        0.0,
        0.0,
    )
    assert second_start.x == pytest.approx(600.0)
    assert second_start.y == pytest.approx(100.0)
    assert second_end.x == pytest.approx(600.0)
    assert second_end.y == pytest.approx(850.0)


def test_split_tool_accepts_point_on_bent_second_straight_run():
    tool = module.InteractiveSplitMemberTool(
        object(),
        bent_member_object(),
    )
    tool.view = FakeView()

    point = tool.resolve_split_point(
        (
            600.0,
            475.0,
        )
    )

    assert point.x == pytest.approx(600.0)
    assert point.y == pytest.approx(475.0)
    assert tool.start_point.x == pytest.approx(600.0)
    assert tool.start_point.y == pytest.approx(100.0)


def test_split_tool_rejects_bent_tangent_point():
    tool = module.InteractiveSplitMemberTool(
        object(),
        bent_member_object(),
    )
    tool.view = FakeView()

    assert (
        tool.resolve_split_point(
            (
                500.0,
                0.0,
            )
        )
        is None
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
