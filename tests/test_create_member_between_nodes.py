"""Tests for ForgeCAD node-to-node member command helpers."""

import sys
import types

import pytest


# ---------------------------------------------------------
# FreeCAD stub
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


class FakeSelection:
    """Minimal FreeCAD selection implementation."""

    selected = []

    @classmethod
    def getSelection(cls):
        return list(
            cls.selected
        )

    @classmethod
    def clearSelection(cls):
        cls.selected = []

    @classmethod
    def addSelection(
        cls,
        obj,
    ):
        cls.selected.append(
            obj
        )


fake_freecad_gui.Selection = (
    FakeSelection
)

fake_freecad_gui.getMainWindow = (
    lambda: None
)

fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)

sys.modules[
    "FreeCADGui"
] = fake_freecad_gui


# ---------------------------------------------------------
# PySide stub
# ---------------------------------------------------------

fake_pyside = types.ModuleType(
    "PySide"
)

fake_qtgui = types.ModuleType(
    "QtGui"
)


class FakeDialog:
    pass


fake_qtgui.QDialog = (
    FakeDialog
)

fake_pyside.QtGui = (
    fake_qtgui
)

sys.modules[
    "PySide"
] = fake_pyside

sys.modules[
    "PySide.QtGui"
] = fake_qtgui


# ---------------------------------------------------------
# Import module against this test's stubs
# ---------------------------------------------------------

sys.modules.pop(
    "forgecad.adapters.freecad.commands.create_member_between_nodes",
    None,
)

from forgecad.adapters.freecad.commands import (
    create_member_between_nodes as command_module,
)


is_forgecad_node = (
    command_module.is_forgecad_node
)

selected_nodes = (
    command_module.selected_nodes
)

node_from_object = (
    command_module.node_from_object
)

next_member_id = (
    command_module.next_member_id
)


# ---------------------------------------------------------
# Test isolation
# ---------------------------------------------------------

@pytest.fixture(
    autouse=True
)
def reset_selection():
    """Reset and rebind the FreeCAD selection stub."""

    FakeSelection.selected = []

    command_module.FreeCADGui = (
        fake_freecad_gui
    )

    command_module.FreeCADGui.Selection = (
        FakeSelection
    )

    yield

    FakeSelection.selected = []


# ---------------------------------------------------------
# Fake objects
# ---------------------------------------------------------

class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


class FakeNodeObject:
    def __init__(
        self,
        node_id,
        position,
    ):
        self.NodeID = node_id
        self.Position = FakeVector(
            *position
        )


class FakeMemberObject:
    def __init__(
        self,
        member_id,
    ):
        self.MemberID = member_id


class FakeUnrelatedObject:
    pass


class FakeFrameGroup:
    def __init__(
        self,
        objects=None,
    ):
        self.Group = list(
            objects or []
        )


# ---------------------------------------------------------
# Node recognition
# ---------------------------------------------------------

def test_forgecad_node_is_recognized():
    node = FakeNodeObject(
        "N001",
        (0, 0, 0),
    )

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


def test_object_missing_node_id_is_rejected():
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


def test_object_missing_position_is_rejected():
    obj = FakeUnrelatedObject()

    obj.NodeID = "N001"

    assert (
        is_forgecad_node(
            obj
        )
        is False
    )


# ---------------------------------------------------------
# Node conversion
# ---------------------------------------------------------

def test_node_from_object_preserves_coordinates():
    obj = FakeNodeObject(
        "N004",
        (
            1200.0,
            450.0,
            300.0,
        ),
    )

    node = node_from_object(
        obj
    )

    assert node.x == pytest.approx(
        1200.0
    )

    assert node.y == pytest.approx(
        450.0
    )

    assert node.z == pytest.approx(
        300.0
    )


# ---------------------------------------------------------
# Node selection
# ---------------------------------------------------------

def test_selected_nodes_returns_exactly_two_nodes():
    node_1 = FakeNodeObject(
        "N001",
        (0, 0, 0),
    )

    node_2 = FakeNodeObject(
        "N002",
        (1000, 0, 0),
    )

    FakeSelection.selected = [
        node_1,
        node_2,
    ]

    assert selected_nodes() == [
        node_1,
        node_2,
    ]


def test_selected_nodes_rejects_single_node():
    FakeSelection.selected = [
        FakeNodeObject(
            "N001",
            (0, 0, 0),
        )
    ]

    assert (
        selected_nodes()
        == []
    )


def test_selected_nodes_rejects_mixed_selection():
    FakeSelection.selected = [
        FakeNodeObject(
            "N001",
            (0, 0, 0),
        ),
        FakeUnrelatedObject(),
    ]

    assert (
        selected_nodes()
        == []
    )


# ---------------------------------------------------------
# Member IDs
# ---------------------------------------------------------

def test_next_member_id_starts_at_m001():
    frame_group = FakeFrameGroup()

    assert (
        next_member_id(
            frame_group
        )
        == "M001"
    )


def test_next_member_id_follows_highest_existing_id():
    frame_group = FakeFrameGroup(
        [
            FakeMemberObject(
                "M001"
            ),
            FakeMemberObject(
                "M004"
            ),
            FakeMemberObject(
                "M002"
            ),
        ]
    )

    assert (
        next_member_id(
            frame_group
        )
        == "M005"
    )


def test_next_member_id_ignores_invalid_ids():
    frame_group = FakeFrameGroup(
        [
            FakeMemberObject(
                "Member"
            ),
            FakeMemberObject(
                "MABC"
            ),
            FakeMemberObject(
                "M007"
            ),
        ]
    )

    assert (
        next_member_id(
            frame_group
        )
        == "M008"
    )
    