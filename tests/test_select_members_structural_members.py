"""Tests for selecting straight and bent ForgeCAD structural members."""

import sys
import types


class FakeQuantity:
    def __init__(
        self,
        value,
    ):
        self.Value = float(
            value
        )

    def __float__(
        self,
    ):
        return self.Value


class FakeMember:
    pass


class FakeGroup:
    def __init__(
        self,
        members,
    ):
        self.Group = list(
            members
        )


class FakeDocument:
    def __init__(
        self,
        members,
    ):
        self.group = FakeGroup(
            members
        )

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADFrame":
            return self.group

        return None


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_selection = types.SimpleNamespace(
    getSelection=lambda: [],
    clearSelection=lambda: None,
    addSelection=lambda obj: None,
)

fake_freecad_gui.Selection = (
    fake_selection
)

fake_freecad_gui.getMainWindow = (
    lambda: None
)

fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)


class FakeWidget:
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        pass


class FakeDialog(
    FakeWidget
):
    pass


fake_qtgui = types.SimpleNamespace(
    QDialog=FakeDialog,
    QComboBox=FakeWidget,
    QLineEdit=FakeWidget,
    QDoubleSpinBox=FakeWidget,
    QStackedWidget=FakeWidget,
    QWidget=FakeWidget,
    QHBoxLayout=FakeWidget,
    QLabel=FakeWidget,
    QFormLayout=FakeWidget,
    QDialogButtonBox=FakeWidget,
    QVBoxLayout=FakeWidget,
    QMessageBox=FakeWidget,
)

fake_pyside = types.ModuleType(
    "PySide"
)
fake_pyside.QtGui = fake_qtgui

fake_part = types.ModuleType(
    "Part"
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

sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad.commands.select_members import (
    frame_members,
    member_length,
    member_name,
    members_with_length_range,
    members_with_name_prefix,
)


def straight_member(
    name="Crossmember 1",
    length=500.0,
):
    member = FakeMember()

    member.MemberID = "M001"
    member.MemberName = name
    member.TubeProfile = (
        "1.750 x .120 DOM"
    )
    member.MemberLength = (
        FakeQuantity(
            length
        )
    )
    member.Material = (
        "A513 Type 5 DOM"
    )

    return member


def bent_member(
    name="Main Hoop",
    length=1500.0,
):
    member = FakeMember()

    member.TubeName = name
    member.TubeProfile = (
        "1.750 x .120 DOM"
    )
    member.Material = (
        "A513 Type 5 DOM"
    )
    member.BendCount = 2
    member.DevelopedLength = (
        FakeQuantity(
            length
        )
    )

    member.StartPoint = object()
    member.InitialDirection = object()
    member.InitialBendNormal = object()

    return member


def test_frame_members_includes_straight_member():
    straight = straight_member()

    document = FakeDocument(
        [
            straight,
        ]
    )

    assert frame_members(
        document
    ) == [
        straight,
    ]


def test_frame_members_includes_bent_member():
    bent = bent_member()

    document = FakeDocument(
        [
            bent,
        ]
    )

    assert frame_members(
        document
    ) == [
        bent,
    ]


def test_frame_members_includes_mixed_structural_members():
    straight = straight_member()
    bent = bent_member()

    document = FakeDocument(
        [
            straight,
            bent,
        ]
    )

    assert frame_members(
        document
    ) == [
        straight,
        bent,
    ]


def test_frame_members_ignores_unrelated_object():
    unrelated = FakeMember()

    unrelated.TubeProfile = (
        "1.750 x .120 DOM"
    )

    document = FakeDocument(
        [
            unrelated,
        ]
    )

    assert frame_members(
        document
    ) == []


def test_member_name_uses_straight_member_name():
    member = straight_member(
        name="Rear Crossmember"
    )

    assert member_name(
        member
    ) == "Rear Crossmember"


def test_member_name_uses_bent_tube_name():
    member = bent_member(
        name="Main Hoop"
    )

    assert member_name(
        member
    ) == "Main Hoop"


def test_name_prefix_matches_straight_member():
    straight = straight_member(
        name="Crossmember 1"
    )

    result = (
        members_with_name_prefix(
            [
                straight,
            ],
            "cross",
        )
    )

    assert result == [
        straight,
    ]


def test_name_prefix_matches_bent_member():
    bent = bent_member(
        name="Main Hoop"
    )

    result = (
        members_with_name_prefix(
            [
                bent,
            ],
            "main",
        )
    )

    assert result == [
        bent,
    ]


def test_member_length_uses_straight_length():
    straight = straight_member(
        length=725.0
    )

    assert member_length(
        straight
    ) == 725.0


def test_member_length_uses_bent_developed_length():
    bent = bent_member(
        length=1825.5
    )

    assert member_length(
        bent
    ) == 1825.5


def test_length_range_matches_bent_and_straight_members():
    short = straight_member(
        name="Short",
        length=500.0,
    )

    bent = bent_member(
        name="Main Hoop",
        length=1500.0,
    )

    long = straight_member(
        name="Long",
        length=2500.0,
    )

    result = (
        members_with_length_range(
            [
                short,
                bent,
                long,
            ],
            1000.0,
            2000.0,
        )
    )

    assert result == [
        bent,
    ]
    