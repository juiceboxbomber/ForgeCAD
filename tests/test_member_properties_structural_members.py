"""Tests for structural-member support in Member Properties."""

import sys
import types


# ---------------------------------------------------------
# Minimal FreeCAD / FreeCADGui / PySide stubs
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.ActiveDocument = object()

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)


class FakeSelection:
    selection = []

    @classmethod
    def getSelection(
        cls,
    ):
        return list(
            cls.selection
        )


fake_freecad_gui.Selection = (
    FakeSelection
)

fake_qt_gui = types.ModuleType(
    "QtGui"
)


class FakeQDialog:
    pass


fake_qt_gui.QDialog = (
    FakeQDialog
)

fake_pyside = types.ModuleType(
    "PySide"
)

fake_pyside.QtGui = (
    fake_qt_gui
)

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = fake_freecad_gui

sys.modules[
    "PySide"
] = fake_pyside

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad.commands.member_properties import (
    is_forgecad_bent_member,
    is_forgecad_member,
    is_forgecad_straight_member,
    member_display_id,
    member_display_length,
    member_display_name,
    member_kind,
)


class FakeStraightMember:
    """Minimal generated straight-member object."""

    MemberID = "M001"
    MemberName = "Front Crossmember"
    TubeProfile = "1.750 x .120 DOM"
    MemberLength = 500.0
    Material = "A513 Type 5 DOM"
    StartPoint = object()
    EndPoint = object()


class FakeBentMember:
    """Minimal generated bent-member object."""

    TubeName = "Main Hoop"
    TubeProfile = "1.750 x .120 DOM"
    Material = "A513 Type 5 DOM"
    BendCount = 2
    DevelopedLength = 1800.0
    StartPoint = object()
    InitialDirection = object()
    InitialBendNormal = object()


class FakeUnrelatedObject:
    """Object that is not a ForgeCAD structural member."""

    Label = "Sketch"


def test_straight_member_is_recognized():
    member = FakeStraightMember()

    assert (
        is_forgecad_straight_member(
            member
        )
        is True
    )

    assert (
        is_forgecad_bent_member(
            member
        )
        is False
    )

    assert (
        is_forgecad_member(
            member
        )
        is True
    )


def test_bent_member_is_recognized():
    member = FakeBentMember()

    assert (
        is_forgecad_straight_member(
            member
        )
        is False
    )

    assert (
        is_forgecad_bent_member(
            member
        )
        is True
    )

    assert (
        is_forgecad_member(
            member
        )
        is True
    )


def test_unrelated_object_is_not_member():
    member = FakeUnrelatedObject()

    assert (
        is_forgecad_member(
            member
        )
        is False
    )


def test_straight_member_kind():
    assert (
        member_kind(
            FakeStraightMember()
        )
        == "Straight"
    )


def test_bent_member_kind():
    assert (
        member_kind(
            FakeBentMember()
        )
        == "Bent"
    )


def test_straight_member_display_name():
    assert (
        member_display_name(
            FakeStraightMember()
        )
        == "Front Crossmember"
    )


def test_bent_member_display_name():
    assert (
        member_display_name(
            FakeBentMember()
        )
        == "Main Hoop"
    )


def test_straight_member_display_id():
    assert (
        member_display_id(
            FakeStraightMember()
        )
        == "M001"
    )


def test_bent_member_has_no_straight_member_id():
    assert (
        member_display_id(
            FakeBentMember()
        )
        == ""
    )


def test_straight_member_display_length():
    assert (
        member_display_length(
            FakeStraightMember()
        )
        == 500.0
    )


def test_bent_member_display_length_uses_developed_length():
    assert (
        member_display_length(
            FakeBentMember()
        )
        == 1800.0
    )
