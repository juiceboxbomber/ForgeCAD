"""Tests for ForgeCAD Select Members command helpers."""

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
    selected = []

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
# Import helpers after stubbing FreeCAD
# ---------------------------------------------------------

from forgecad.adapters.freecad.commands.select_members import (
    frame_members,
    members_with_profile,
)


class FakeMember:
    def __init__(
        self,
        member_id,
        profile,
    ):
        self.MemberID = member_id
        self.TubeProfile = profile


class FakeUnrelatedObject:
    pass


class FakeFrameGroup:
    def __init__(
        self,
        objects,
    ):
        self.Group = list(
            objects
        )


class FakeDocument:
    def __init__(
        self,
        frame_objects=None,
    ):
        self.frame_group = (
            None
            if frame_objects is None
            else FakeFrameGroup(
                frame_objects
            )
        )

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADFrame":
            return self.frame_group

        return None


def test_frame_members_returns_empty_for_none_document():
    assert (
        frame_members(
            None
        )
        == []
    )


def test_frame_members_returns_empty_when_frame_group_missing():
    document = FakeDocument(
        frame_objects=None
    )

    assert (
        frame_members(
            document
        )
        == []
    )


def test_frame_members_returns_generated_members():
    member_1 = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )

    member_2 = FakeMember(
        "M002",
        "1.000 x .065 DOM",
    )

    document = FakeDocument(
        [
            member_1,
            member_2,
        ]
    )

    assert (
        frame_members(
            document
        )
        == [
            member_1,
            member_2,
        ]
    )


def test_frame_members_ignores_unrelated_objects():
    member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )

    document = FakeDocument(
        [
            FakeUnrelatedObject(),
            member,
        ]
    )

    assert (
        frame_members(
            document
        )
        == [
            member
        ]
    )


def test_frame_members_requires_member_id():
    obj = FakeUnrelatedObject()
    obj.TubeProfile = (
        "1.750 x .120 DOM"
    )

    document = FakeDocument(
        [obj]
    )

    assert (
        frame_members(
            document
        )
        == []
    )


def test_frame_members_requires_tube_profile():
    obj = FakeUnrelatedObject()
    obj.MemberID = "M001"

    document = FakeDocument(
        [obj]
    )

    assert (
        frame_members(
            document
        )
        == []
    )


def test_members_with_profile_returns_matching_members():
    member_1 = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )

    member_2 = FakeMember(
        "M002",
        "1.000 x .065 DOM",
    )

    member_3 = FakeMember(
        "M003",
        "1.750 x .120 DOM",
    )

    result = members_with_profile(
        [
            member_1,
            member_2,
            member_3,
        ],
        "1.750 x .120 DOM",
    )

    assert result == [
        member_1,
        member_3,
    ]


def test_members_with_profile_returns_empty_when_no_match():
    member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )

    assert (
        members_with_profile(
            [member],
            "1.000 x .065 DOM",
        )
        == []
    )


def test_members_with_profile_preserves_member_order():
    member_3 = FakeMember(
        "M003",
        "1.250 x .095 DOM",
    )

    member_1 = FakeMember(
        "M001",
        "1.250 x .095 DOM",
    )

    member_7 = FakeMember(
        "M007",
        "1.250 x .095 DOM",
    )

    result = members_with_profile(
        [
            member_3,
            member_1,
            member_7,
        ],
        "1.250 x .095 DOM",
    )

    assert result == [
        member_3,
        member_1,
        member_7,
    ]


def test_members_with_profile_does_not_modify_input():
    members = [
        FakeMember(
            "M001",
            "1.750 x .120 DOM",
        ),
        FakeMember(
            "M002",
            "1.000 x .065 DOM",
        ),
    ]

    original = list(
        members
    )

    members_with_profile(
        members,
        "1.750 x .120 DOM",
    )

    assert members == original
    