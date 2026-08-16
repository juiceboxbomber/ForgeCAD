"""Tests for layout reuse in Create Member Between Nodes."""

import sys
import types


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(
            x
        )
        self.y = float(
            y
        )
        self.z = float(
            z
        )


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.Vector = FakeVector
fake_freecad.ActiveDocument = None

fake_gui = types.ModuleType(
    "FreeCADGui"
)
fake_gui.Selection = types.SimpleNamespace(
    getSelection=lambda: [],
    clearSelection=lambda: None,
    addSelection=lambda obj: None,
)
fake_gui.getMainWindow = (
    lambda: None
)
fake_gui.addCommand = (
    lambda *args, **kwargs: None
)

fake_pyside = types.ModuleType(
    "PySide"
)


class FakeDialog:
    pass


fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=FakeDialog,
)

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "FreeCADGui"
] = fake_gui
sys.modules[
    "PySide"
] = fake_pyside
sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad.commands.create_member_between_nodes import (
    existing_layout_object,
    layout_object_matches_points,
    point_key,
)


class FakeLayoutObject:
    def __init__(
        self,
        start,
        end,
    ):
        self.StartPoint = FakeVector(
            *start
        )
        self.EndPoint = FakeVector(
            *end
        )


class FakeGroup:
    def __init__(
        self,
        objects,
    ):
        self.Group = list(
            objects
        )


def test_point_key_rounds_coordinates():
    key = point_key(
        FakeVector(
            1.0000004,
            2.0,
            3.0,
        )
    )

    assert key == (
        1.0,
        2.0,
        3.0,
    )


def test_layout_match_accepts_same_direction():
    layout = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    assert layout_object_matches_points(
        layout,
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            1000,
            0,
            0,
        ),
    )


def test_layout_match_accepts_reversed_direction():
    layout = FakeLayoutObject(
        (1000, 0, 0),
        (0, 0, 0),
    )

    assert layout_object_matches_points(
        layout,
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            1000,
            0,
            0,
        ),
    )


def test_layout_match_rejects_different_connection():
    layout = FakeLayoutObject(
        (0, 0, 0),
        (500, 0, 0),
    )

    assert not layout_object_matches_points(
        layout,
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            1000,
            0,
            0,
        ),
    )


def test_existing_layout_object_reuses_matching_line():
    first = FakeLayoutObject(
        (0, 0, 0),
        (500, 0, 0),
    )

    matching = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    group = FakeGroup(
        [
            first,
            matching,
        ]
    )

    result = existing_layout_object(
        group,
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            1000,
            0,
            0,
        ),
    )

    assert result is matching


def test_existing_layout_object_returns_none_without_match():
    group = FakeGroup(
        [
            FakeLayoutObject(
                (0, 0, 0),
                (500, 0, 0),
            ),
        ]
    )

    result = existing_layout_object(
        group,
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            1000,
            0,
            0,
        ),
    )

    assert result is None
