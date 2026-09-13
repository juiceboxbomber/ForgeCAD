"""Tests for the interactive FreeCAD Trim/Extend command."""

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

    @staticmethod
    def information(
        *args,
        **kwargs,
    ):
        return None


class FakeQTimer:
    calls = []

    @staticmethod
    def singleShot(
        delay,
        callback,
    ):
        FakeQTimer.calls.append(
            (
                delay,
                callback,
            )
        )


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
    addObserver=lambda observer: None,
    removeObserver=lambda observer: None,
)
fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)

fake_part = types.ModuleType(
    "Part"
)

fake_pyside = types.ModuleType(
    "PySide"
)
fake_pyside.QtCore = SimpleNamespace(
    QTimer=FakeQTimer,
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
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.adapters.freecad.commands import (
    trim_extend_member as module,
)


class FakeView:
    def __init__(
        self,
    ):
        self.added = []
        self.removed = []
        self.next_handle = 1

    def getPointOnScreen(
        self,
        vector,
    ):
        return (
            vector.x,
            vector.y,
        )

    def addEventCallback(
        self,
        event_type,
        callback,
    ):
        handle = (
            f"handle-{self.next_handle}"
        )

        self.next_handle += 1

        self.added.append(
            (
                event_type,
                handle,
            )
        )

        return handle

    def removeEventCallback(
        self,
        event_type,
        handle,
    ):
        self.removed.append(
            (
                event_type,
                handle,
            )
        )


def make_member(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=TubeProfile(
            outside_diameter=44.45,
            wall_thickness=3.048,
        ),
        material=Material(
            name="DOM Steel",
            density=7850.0,
            yield_strength=350.0,
        ),
    )


def make_tool_without_init():
    tool = object.__new__(
        module.InteractiveTrimExtendTool
    )

    tool.document = None
    tool.source_object = None
    tool.source_member = None
    tool.view = None
    tool.status_bar = None
    tool.selection_observer = None
    tool.keyboard_callback = None
    tool.trim_click_callback = None
    tool.target_object = None
    tool.intersection = None
    tool.source_parameter = None
    tool.stopped = False
    tool.commit_pending = False

    return tool


def test_member_detection_requires_member_metadata():
    assert module.is_forgecad_member(
        SimpleNamespace(
            MemberID="M001",
            StartPoint=object(),
            EndPoint=object(),
        )
    )

    assert not module.is_forgecad_member(
        SimpleNamespace(
            StartPoint=object(),
            EndPoint=object(),
        )
    )


def test_nearest_screen_endpoint_selects_start():
    source = make_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    result = (
        module.endpoint_nearest_screen_position(
            FakeView(),
            source,
            (
                100.0,
                20.0,
            ),
        )
    )

    assert result == "start"


def test_nearest_screen_endpoint_selects_end():
    source = make_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    result = (
        module.endpoint_nearest_screen_position(
            FakeView(),
            source,
            (
                900.0,
                20.0,
            ),
        )
    )

    assert result == "end"


def test_nearest_endpoint_uses_screen_projection_for_3d_member():
    source = make_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            500.0,
        ),
    )

    result = (
        module.endpoint_nearest_screen_position(
            FakeView(),
            source,
            (
                950.0,
                0.0,
            ),
        )
    )

    assert result == "end"


def test_screen_distance_squared():
    assert (
        module.screen_distance_squared(
            (
                0.0,
                0.0,
            ),
            (
                3.0,
                4.0,
            ),
        )
        == pytest.approx(
            25.0
        )
    )


def test_selection_observer_forwards_selected_object():
    calls = []

    tool = SimpleNamespace(
        target_selected=lambda document_name, object_name: calls.append(
            (
                document_name,
                object_name,
            )
        )
    )

    observer = (
        module.TrimExtendSelectionObserver(
            tool
        )
    )

    observer.addSelection(
        "Doc",
        "Member001",
        "",
        None,
    )

    assert calls == [
        (
            "Doc",
            "Member001",
        )
    ]


def test_keyboard_and_mouse_callbacks_use_separate_handles():
    tool = make_tool_without_init()
    tool.view = FakeView()

    tool.add_keyboard_callback()
    tool.add_trim_click_callback()

    keyboard_handle = (
        tool.keyboard_callback
    )

    mouse_handle = (
        tool.trim_click_callback
    )

    assert keyboard_handle != mouse_handle

    tool.remove_trim_click_callback()
    tool.remove_keyboard_callback()

    assert tool.view.removed == [
        (
            "SoMouseButtonEvent",
            mouse_handle,
        ),
        (
            "SoKeyboardEvent",
            keyboard_handle,
        ),
    ]


def test_stop_removes_both_callback_types_and_clears_status():
    class StatusBar:
        def __init__(
            self,
        ):
            self.cleared = False

        def clearMessage(
            self,
        ):
            self.cleared = True

    tool = make_tool_without_init()

    view = FakeView()

    tool.view = view
    tool.status_bar = StatusBar()

    tool.add_keyboard_callback()
    tool.add_trim_click_callback()

    keyboard_handle = (
        tool.keyboard_callback
    )

    mouse_handle = (
        tool.trim_click_callback
    )

    tool.stop()

    assert (
        "SoMouseButtonEvent",
        mouse_handle,
    ) in view.removed

    assert (
        "SoKeyboardEvent",
        keyboard_handle,
    ) in view.removed

    assert tool.status_bar is None
    assert tool.view is None
    assert tool.stopped is True


def test_escape_defers_stop_until_callback_returns(
    monkeypatch,
):
    calls = []

    tool = make_tool_without_init()

    monkeypatch.setattr(
        module,
        "defer_call",
        lambda callback: calls.append(
            callback
        ),
    )

    tool.on_keyboard_event(
        {
            "State": "DOWN",
            "Key": "ESCAPE",
        }
    )

    assert tool.stopped is False
    assert len(
        calls
    ) == 1

    calls[
        0
    ]()

    assert tool.stopped is True


def test_trim_click_defers_commit_and_removes_mouse_callback(
    monkeypatch,
):
    source = make_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    tool = make_tool_without_init()
    tool.source_member = source
    tool.view = FakeView()
    tool.add_trim_click_callback()

    deferred = []
    committed = []

    monkeypatch.setattr(
        module,
        "defer_call",
        lambda callback: deferred.append(
            callback
        ),
    )

    tool.commit = (
        lambda endpoint: committed.append(
            endpoint
        )
    )

    tool.on_trim_side_click(
        {
            "State": "DOWN",
            "Button": "BUTTON1",
            "Position": (
                900.0,
                0.0,
            ),
        }
    )

    assert tool.commit_pending is True
    assert tool.trim_click_callback is None

    assert any(
        event_type
        == "SoMouseButtonEvent"
        for event_type, _handle
        in tool.view.removed
    )

    assert committed == []

    deferred[
        0
    ]()

    assert committed == [
        "end"
    ]


def test_defer_call_uses_zero_delay_qt_timer():
    FakeQTimer.calls.clear()

    called = []

    module.defer_call(
        lambda: called.append(
            True
        )
    )

    assert len(
        FakeQTimer.calls
    ) == 1

    delay, callback = (
        FakeQTimer.calls[
            0
        ]
    )

    assert delay == 0
    assert called == []

    callback()

    assert called == [
        True
    ]
