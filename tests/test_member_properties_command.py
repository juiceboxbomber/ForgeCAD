"""Tests for ForgeCAD Member Properties command helpers."""

import sys
import types

import pytest


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
# FreeCADGui stubs
# ---------------------------------------------------------

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)


class FakeSelection:
    """Minimal FreeCAD selection stub."""

    selected = []

    @classmethod
    def getSelection(cls):
        return list(
            cls.selected
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
# PySide stubs
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
# Import module under test against this file's stubs
# ---------------------------------------------------------

sys.modules.pop(
    "forgecad.adapters.freecad.commands.member_properties",
    None,
)

from forgecad.adapters.freecad.commands import (
    member_properties as member_properties_module,
)


build_bulk_member_names = (
    member_properties_module.build_bulk_member_names
)

is_forgecad_member = (
    member_properties_module.is_forgecad_member
)

selected_member = (
    member_properties_module.selected_member
)

selected_members = (
    member_properties_module.selected_members
)


# ---------------------------------------------------------
# Test isolation
# ---------------------------------------------------------

@pytest.fixture(
    autouse=True
)
def reset_freecad_gui_selection():
    """
    Force the command module to use this test file's selection stub.

    Other FreeCAD adapter tests also install fake FreeCADGui modules.
    This prevents test collection order from changing these results.
    """

    FakeSelection.selected = []

    member_properties_module.FreeCADGui = (
        fake_freecad_gui
    )

    member_properties_module.FreeCADGui.Selection = (
        FakeSelection
    )

    yield

    FakeSelection.selected = []


# ---------------------------------------------------------
# Fake objects
# ---------------------------------------------------------

class FakeMember:
    """Object containing the required ForgeCAD member properties."""

    def __init__(
        self,
        member_id="M001",
        member_name="Left Main Rail",
    ):
        self.MemberID = member_id
        self.MemberName = member_name
        self.TubeProfile = "1.750 x .120 DOM"
        self.MemberLength = 1000.0
        self.Material = "A513 Type 5 DOM"


class FakeLayoutLine:
    """Layout object that must not be treated as a generated member."""

    def __init__(self):
        self.MemberName = "Left Main Rail"
        self.TubeProfileOverride = (
            "1.750 x .120 DOM"
        )
        self.LayoutLength = 1000.0


class FakeUnrelatedObject:
    """Non-ForgeCAD object."""

    pass


# ---------------------------------------------------------
# ForgeCAD member detection
# ---------------------------------------------------------

def test_generated_member_is_recognized():
    member = FakeMember()

    assert (
        is_forgecad_member(
            member
        )
        is True
    )


def test_none_is_not_member():
    assert (
        is_forgecad_member(
            None
        )
        is False
    )


def test_layout_line_is_not_member():
    layout_line = (
        FakeLayoutLine()
    )

    assert (
        is_forgecad_member(
            layout_line
        )
        is False
    )


def test_unrelated_object_is_not_member():
    obj = (
        FakeUnrelatedObject()
    )

    assert (
        is_forgecad_member(
            obj
        )
        is False
    )


def test_member_missing_required_property_is_rejected():
    member = FakeMember()

    del member.MemberID

    assert (
        is_forgecad_member(
            member
        )
        is False
    )


# ---------------------------------------------------------
# Single-member selection
# ---------------------------------------------------------

def test_selected_member_returns_single_member():
    member = FakeMember()

    FakeSelection.selected = [
        member
    ]

    assert (
        selected_member()
        is member
    )


def test_selected_member_returns_none_for_no_selection():
    FakeSelection.selected = []

    assert (
        selected_member()
        is None
    )


def test_selected_member_returns_none_for_multiple_selection():
    FakeSelection.selected = [
        FakeMember(
            "M001"
        ),
        FakeMember(
            "M002"
        ),
    ]

    assert (
        selected_member()
        is None
    )


def test_selected_member_returns_none_for_layout_line():
    FakeSelection.selected = [
        FakeLayoutLine()
    ]

    assert (
        selected_member()
        is None
    )


def test_selected_member_returns_none_for_unrelated_object():
    FakeSelection.selected = [
        FakeUnrelatedObject()
    ]

    assert (
        selected_member()
        is None
    )


# ---------------------------------------------------------
# Multi-member selection
# ---------------------------------------------------------

def test_selected_members_returns_all_selected_members():
    member_1 = FakeMember(
        "M001"
    )

    member_2 = FakeMember(
        "M002"
    )

    member_3 = FakeMember(
        "M003"
    )

    FakeSelection.selected = [
        member_1,
        member_2,
        member_3,
    ]

    result = (
        selected_members()
    )

    assert result == [
        member_1,
        member_2,
        member_3,
    ]


def test_selected_members_returns_single_member_as_list():
    member = FakeMember()

    FakeSelection.selected = [
        member
    ]

    assert (
        selected_members()
        == [member]
    )


def test_selected_members_returns_empty_for_no_selection():
    FakeSelection.selected = []

    assert (
        selected_members()
        == []
    )


def test_selected_members_rejects_layout_line():
    FakeSelection.selected = [
        FakeLayoutLine()
    ]

    assert (
        selected_members()
        == []
    )


def test_selected_members_rejects_unrelated_object():
    FakeSelection.selected = [
        FakeUnrelatedObject()
    ]

    assert (
        selected_members()
        == []
    )


def test_selected_members_rejects_mixed_selection():
    FakeSelection.selected = [
        FakeMember(
            "M001"
        ),
        FakeLayoutLine(),
    ]

    assert (
        selected_members()
        == []
    )


def test_selected_members_rejects_member_and_unrelated_object():
    FakeSelection.selected = [
        FakeMember(
            "M001"
        ),
        FakeUnrelatedObject(),
    ]

    assert (
        selected_members()
        == []
    )


# ---------------------------------------------------------
# Bulk member naming
# ---------------------------------------------------------

def test_bulk_names_start_at_one_by_default():
    members = [
        FakeMember(
            "M001"
        ),
        FakeMember(
            "M002"
        ),
        FakeMember(
            "M003"
        ),
    ]

    assignments = (
        build_bulk_member_names(
            members,
            "Crossmember",
        )
    )

    assert assignments == [
        (
            members[0],
            "Crossmember 1",
        ),
        (
            members[1],
            "Crossmember 2",
        ),
        (
            members[2],
            "Crossmember 3",
        ),
    ]


def test_bulk_names_support_custom_start_number():
    members = [
        FakeMember(
            "M004"
        ),
        FakeMember(
            "M005"
        ),
        FakeMember(
            "M006"
        ),
    ]

    assignments = (
        build_bulk_member_names(
            members,
            "Roof Bar",
            start_number=5,
        )
    )

    assert assignments == [
        (
            members[0],
            "Roof Bar 5",
        ),
        (
            members[1],
            "Roof Bar 6",
        ),
        (
            members[2],
            "Roof Bar 7",
        ),
    ]


def test_bulk_names_trim_prefix_whitespace():
    members = [
        FakeMember(
            "M001"
        ),
        FakeMember(
            "M002"
        ),
    ]

    assignments = (
        build_bulk_member_names(
            members,
            "   Door Bar   ",
        )
    )

    assert assignments == [
        (
            members[0],
            "Door Bar 1",
        ),
        (
            members[1],
            "Door Bar 2",
        ),
    ]


def test_bulk_names_empty_prefix_returns_no_assignments():
    members = [
        FakeMember(
            "M001"
        ),
        FakeMember(
            "M002"
        ),
    ]

    assert (
        build_bulk_member_names(
            members,
            "",
        )
        == []
    )


def test_bulk_names_whitespace_only_prefix_returns_no_assignments():
    members = [
        FakeMember(
            "M001"
        )
    ]

    assert (
        build_bulk_member_names(
            members,
            "     ",
        )
        == []
    )


def test_bulk_names_preserve_member_order():
    member_7 = FakeMember(
        "M007"
    )

    member_2 = FakeMember(
        "M002"
    )

    member_5 = FakeMember(
        "M005"
    )

    members = [
        member_7,
        member_2,
        member_5,
    ]

    assignments = (
        build_bulk_member_names(
            members,
            "Brace",
        )
    )

    assert assignments[0] == (
        member_7,
        "Brace 1",
    )

    assert assignments[1] == (
        member_2,
        "Brace 2",
    )

    assert assignments[2] == (
        member_5,
        "Brace 3",
    )


def test_building_bulk_names_does_not_modify_members():
    member_1 = FakeMember(
        "M001",
        "Original One",
    )

    member_2 = FakeMember(
        "M002",
        "Original Two",
    )

    build_bulk_member_names(
        [
            member_1,
            member_2,
        ],
        "Crossmember",
    )

    assert (
        member_1.MemberName
        == "Original One"
    )

    assert (
        member_2.MemberName
        == "Original Two"
    )
    