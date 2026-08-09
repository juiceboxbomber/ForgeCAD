"""Tests for ForgeCAD Member Properties command helpers."""

import sys
import types


# ---------------------------------------------------------
# FreeCAD stubs
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.ActiveDocument = None

sys.modules.setdefault(
    "FreeCAD",
    fake_freecad,
)


# ---------------------------------------------------------
# Part stub
# ---------------------------------------------------------

fake_part = types.ModuleType(
    "Part"
)

sys.modules.setdefault(
    "Part",
    fake_part,
)


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

sys.modules.setdefault(
    "FreeCADGui",
    fake_freecad_gui,
)


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

sys.modules.setdefault(
    "PySide",
    fake_pyside,
)

sys.modules.setdefault(
    "PySide.QtGui",
    fake_qtgui,
)


# ---------------------------------------------------------
# Import command helpers after stubbing FreeCAD
# ---------------------------------------------------------

from forgecad.adapters.freecad.commands.member_properties import (
    is_forgecad_member,
    selected_member,
    selected_members,
)


class FakeMember:
    """Object containing the required ForgeCAD member properties."""

    def __init__(
        self,
        member_id="M001",
    ):
        self.MemberID = member_id
        self.MemberName = "Left Main Rail"
        self.TubeProfile = "1.750 x .120 DOM"
        self.MemberLength = 1000.0
        self.Material = "A513 Type 5 DOM"


class FakeLayoutLine:
    """Layout object that must not be treated as a generated member."""

    def __init__(self):
        self.MemberName = "Left Main Rail"
        self.TubeProfileOverride = "1.750 x .120 DOM"
        self.LayoutLength = 1000.0


class FakeUnrelatedObject:
    """Non-ForgeCAD object."""

    pass


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
        FakeMember("M001"),
        FakeMember("M002"),
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
    