"""Tests for the ForgeCAD Create Upright command."""

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


fake_freecad = types.ModuleType("FreeCAD")
fake_freecad.Vector = FakeVector
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType("FreeCADGui")
fake_freecad_gui.Selection = SimpleNamespace(
    getSelection=lambda: [],
    clearSelection=lambda: None,
    addSelection=lambda obj: None,
)
fake_freecad_gui.addCommand = lambda *args, **kwargs: None
fake_freecad_gui.getMainWindow = lambda: None

fake_part = types.ModuleType("Part")

fake_pyside = types.ModuleType("PySide")
fake_pyside.QtCore = SimpleNamespace()
fake_pyside.QtGui = SimpleNamespace(
    QDialog=FakeQDialog,
    QMessageBox=FakeQMessageBox,
)

sys.modules["FreeCAD"] = fake_freecad
sys.modules["FreeCADGui"] = fake_freecad_gui
sys.modules["Part"] = fake_part
sys.modules["PySide"] = fake_pyside

fake_draw_member_interactive = types.ModuleType(
    "forgecad.adapters.freecad.commands.draw_member_interactive"
)

fake_draw_member_interactive.get_or_create_node = (
    lambda document, point: None
)

_draw_member_module_name = (
    "forgecad.adapters.freecad.commands.draw_member_interactive"
)

_previous_draw_member_module = sys.modules.get(
    _draw_member_module_name
)

sys.modules[
    _draw_member_module_name
] = fake_draw_member_interactive

try:
    from forgecad.geometry import Point3D
    from forgecad.adapters.freecad.commands import create_upright as module

finally:
    if _previous_draw_member_module is None:
        sys.modules.pop(
            _draw_member_module_name,
            None,
        )
    else:
        sys.modules[
            _draw_member_module_name
        ] = _previous_draw_member_module


class FakeDocument:
    def __init__(self):
        self.recompute_count = 0

    def recompute(self):
        self.recompute_count += 1


def test_upright_end_point_uses_global_positive_z():
    result = module.upright_end_point(
        Point3D(
            100.0,
            200.0,
            300.0,
        ),
        500.0,
    )

    assert result == Point3D(
        100.0,
        200.0,
        800.0,
    )


def test_upright_height_must_be_positive():
    try:
        module.upright_end_point(
            Point3D(
                0.0,
                0.0,
                0.0,
            ),
            0.0,
        )
    except ValueError as error:
        assert "greater than zero" in str(
            error
        )
    else:
        raise AssertionError(
            "Expected zero height to fail."
        )


def test_create_upright_reuses_normal_node_and_member_creation(
    monkeypatch,
):
    document = FakeDocument()

    start = Point3D(
        10.0,
        20.0,
        30.0,
    )

    created_points = []
    events = []

    def fake_get_or_create_node(
        doc,
        point,
    ):
        created_points.append(
            point
        )

        return SimpleNamespace(
            Position=point
        )

    monkeypatch.setattr(
        module,
        "get_or_create_node",
        fake_get_or_create_node,
    )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        lambda doc, start_node, end_node, refresh=False: (
            events.append(
                (
                    "create-member",
                    refresh,
                )
            )
            or (
                "layout",
                "member",
            )
        ),
    )

    monkeypatch.setattr(
        module,
        "refresh_joint_topology",
        lambda doc: (
            events.append(
                "refresh-joints"
            )
            or (
                (),
                (),
            )
        ),
    )

    monkeypatch.setattr(
        module,
        "refresh_fabrication_for_document",
        lambda doc: (
            events.append(
                "refresh-fabrication"
            )
            or ()
        ),
    )

    result = module.create_upright(
        document,
        start,
        400.0,
    )

    assert created_points == [
        Point3D(
            10.0,
            20.0,
            30.0,
        ),
        Point3D(
            10.0,
            20.0,
            430.0,
        ),
    ]

    assert result[
        0
    ] == "layout"

    assert result[
        1
    ] == "member"

    assert events == [
        (
            "create-member",
            False,
        ),
        "refresh-joints",
        "refresh-fabrication",
    ]

    assert document.recompute_count == 2


def test_resolve_point_accepts_member_endpoint(
    monkeypatch,
):
    tool = (
        module.InteractiveCreateUprightTool.__new__(
            module.InteractiveCreateUprightTool
        )
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

    expected = Point3D(
        0.0,
        0.0,
        0.0,
    )

    monkeypatch.setattr(
        module,
        "screen_point_on_segment",
        lambda view, position, start, end: (
            expected,
            2.0,
            0.0,
        ),
    )

    distances = iter(
        [
            1.0,
            100.0,
            100.0,
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

    assert tool.resolve_point(
        (
            100,
            100,
        )
    ) == expected

    assert tool.current_snap_label == (
        "Endpoint"
    )


def test_resolve_point_rejects_cursor_too_far_from_member(
    monkeypatch,
):
    tool = module.InteractiveCreateUprightTool.__new__(
        module.InteractiveCreateUprightTool
    )

    tool.source_member = SimpleNamespace(
        OutsideDiameter=44.45,
    )

    tool.view = object()
    tool.current_snap_label = None

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

    monkeypatch.setattr(
        module,
        "screen_point_on_segment",
        lambda view, position, start, end: (
            Point3D(
                500.0,
                0.0,
                0.0,
            ),
            (
                module.SNAP_DISTANCE_PIXELS
                + 1.0
            ),
            0.5,
        ),
    )

    assert tool.resolve_point(
        (
            100,
            100,
        )
    ) is None


def test_command_name_is_stable():
    assert module.COMMAND_NAME == "ForgeCAD_CreateUpright"
