"""Tests for ForgeCAD Create Upright snapping."""

import sys
import types
from types import SimpleNamespace


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


class FakeQDialog:
    Accepted = 1


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
fake_freecad.Vector = FakeVector
fake_freecad.ActiveDocument = None

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
fake_freecad_gui.getMainWindow = (
    lambda: None
)

fake_part = types.ModuleType(
    "Part"
)

fake_pyside = types.ModuleType(
    "PySide"
)
fake_pyside.QtCore = SimpleNamespace()
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

fake_draw_member_interactive = types.ModuleType(
    "forgecad.adapters.freecad.commands.draw_member_interactive"
)
fake_draw_member_interactive.get_or_create_node = (
    lambda document, point: None
)

_draw_module_name = (
    "forgecad.adapters.freecad.commands.draw_member_interactive"
)

_previous_draw_module = sys.modules.get(
    _draw_module_name
)

sys.modules[
    _draw_module_name
] = fake_draw_member_interactive

try:
    from forgecad.geometry import Point3D
    from forgecad.adapters.freecad.commands import (
        create_upright as module,
    )
finally:
    if _previous_draw_module is None:
        sys.modules.pop(
            _draw_module_name,
            None,
        )
    else:
        sys.modules[
            _draw_module_name
        ] = _previous_draw_module


def test_point_at_parameter_uses_true_3d_centerline():
    result = module.point_at_parameter(
        Point3D(
            0.0,
            0.0,
            0.0,
        ),
        Point3D(
            100.0,
            200.0,
            300.0,
        ),
        0.5,
    )

    assert result == Point3D(
        50.0,
        100.0,
        150.0,
    )


def test_half_od_candidates_use_member_radius():
    member = SimpleNamespace(
        OutsideDiameter=44.45,
    )

    candidates = (
        module.upright_snap_candidates(
            member,
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

    assert candidates[
        0
    ] == (
        0.0,
        "Endpoint",
    )

    assert candidates[
        1
    ] == (
        1.0,
        "Endpoint",
    )

    assert abs(
        candidates[
            2
        ][
            0
        ]
        - 0.022225
    ) < 1e-9

    assert "22.225" in candidates[
        2
    ][
        1
    ]

    assert abs(
        candidates[
            3
        ][
            0
        ]
        - 0.977775
    ) < 1e-9

    assert candidates[
        4
    ] == (
        0.5,
        "Midpoint",
    )


def test_endpoint_has_priority_over_half_od(
    monkeypatch,
):
    tool = module.InteractiveCreateUprightTool.__new__(
        module.InteractiveCreateUprightTool
    )

    tool.source_member = SimpleNamespace(
        OutsideDiameter=44.45,
    )
    tool.view = object()
    tool.start_point = Point3D(
        0.0,
        0.0,
        0.0,
    )
    tool.end_point = Point3D(
        1000.0,
        0.0,
        0.0,
    )
    tool.current_snap_label = None

    monkeypatch.setattr(
        module,
        "screen_point_on_segment",
        lambda view, position, start, end: (
            Point3D(
                10.0,
                0.0,
                0.0,
            ),
            1.0,
            0.01,
        ),
    )

    distances = iter(
        [
            2.0,
            100.0,
            3.0,
            100.0,
            100.0,
        ]
    )

    monkeypatch.setattr(
        module,
        "screen_distance_to_point",
        lambda view, position, point: next(
            distances
        ),
    )

    result = tool.resolve_point(
        (
            10,
            10,
        )
    )

    assert result == Point3D(
        0.0,
        0.0,
        0.0,
    )

    assert tool.current_snap_label == (
        "Endpoint"
    )


def test_half_od_snap_is_selected_when_near_radius_point(
    monkeypatch,
):
    tool = module.InteractiveCreateUprightTool.__new__(
        module.InteractiveCreateUprightTool
    )

    tool.source_member = SimpleNamespace(
        OutsideDiameter=44.45,
    )
    tool.view = object()
    tool.start_point = Point3D(
        0.0,
        0.0,
        0.0,
    )
    tool.end_point = Point3D(
        1000.0,
        0.0,
        0.0,
    )
    tool.current_snap_label = None

    monkeypatch.setattr(
        module,
        "screen_point_on_segment",
        lambda view, position, start, end: (
            Point3D(
                22.0,
                0.0,
                0.0,
            ),
            1.0,
            0.022,
        ),
    )

    distances = iter(
        [
            100.0,
            100.0,
            2.0,
            100.0,
            100.0,
        ]
    )

    monkeypatch.setattr(
        module,
        "screen_distance_to_point",
        lambda view, position, point: next(
            distances
        ),
    )

    result = tool.resolve_point(
        (
            10,
            10,
        )
    )

    assert abs(
        result.x
        - 22.225
    ) < 1e-9

    assert "1/2 OD snap" in (
        tool.current_snap_label
    )


def test_midpoint_snap_is_selected(
    monkeypatch,
):
    tool = module.InteractiveCreateUprightTool.__new__(
        module.InteractiveCreateUprightTool
    )

    tool.source_member = SimpleNamespace(
        OutsideDiameter=44.45,
    )
    tool.view = object()
    tool.start_point = Point3D(
        0.0,
        0.0,
        0.0,
    )
    tool.end_point = Point3D(
        1000.0,
        0.0,
        0.0,
    )
    tool.current_snap_label = None

    monkeypatch.setattr(
        module,
        "screen_point_on_segment",
        lambda view, position, start, end: (
            Point3D(
                495.0,
                0.0,
                0.0,
            ),
            1.0,
            0.495,
        ),
    )

    distances = iter(
        [
            100.0,
            100.0,
            100.0,
            100.0,
            3.0,
        ]
    )

    monkeypatch.setattr(
        module,
        "screen_distance_to_point",
        lambda view, position, point: next(
            distances
        ),
    )

    result = tool.resolve_point(
        (
            10,
            10,
        )
    )

    assert result == Point3D(
        500.0,
        0.0,
        0.0,
    )

    assert tool.current_snap_label == (
        "Midpoint"
    )


def test_free_position_remains_available(
    monkeypatch,
):
    tool = module.InteractiveCreateUprightTool.__new__(
        module.InteractiveCreateUprightTool
    )

    tool.source_member = SimpleNamespace(
        OutsideDiameter=44.45,
    )
    tool.view = object()
    tool.start_point = Point3D(
        0.0,
        0.0,
        0.0,
    )
    tool.end_point = Point3D(
        1000.0,
        0.0,
        0.0,
    )
    tool.current_snap_label = None

    free_point = Point3D(
        317.462,
        0.0,
        0.0,
    )

    monkeypatch.setattr(
        module,
        "screen_point_on_segment",
        lambda view, position, start, end: (
            free_point,
            2.0,
            0.317462,
        ),
    )

    monkeypatch.setattr(
        module,
        "screen_distance_to_point",
        lambda view, position, point: 100.0,
    )

    result = tool.resolve_point(
        (
            10,
            10,
        )
    )

    assert result == free_point
    assert tool.current_snap_label == (
        "Free position"
    )
