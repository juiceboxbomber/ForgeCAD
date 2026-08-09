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
    available_materials,
    frame_members,
    members_with_length_range,
    members_with_material,
    members_with_name_prefix,
    members_with_profile,
)

# ---------------------------------------------------------
# Material filtering
# ---------------------------------------------------------


def test_members_with_material_returns_matches():
    member_1 = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )
    member_1.Material = "A513 Type 5 DOM"

    member_2 = FakeMember(
        "M002",
        "1.750 x .120 DOM",
    )
    member_2.Material = "4130 Chromoly"

    member_3 = FakeMember(
        "M003",
        "1.000 x .065 DOM",
    )
    member_3.Material = "A513 Type 5 DOM"

    result = members_with_material(
        [
            member_1,
            member_2,
            member_3,
        ],
        "A513 Type 5 DOM",
    )

    assert result == [
        member_1,
        member_3,
    ]


def test_members_with_material_is_case_insensitive():
    member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )
    member.Material = "A513 Type 5 DOM"

    assert members_with_material(
        [member],
        "a513 type 5 dom",
    ) == [member]


def test_members_with_material_returns_empty_for_blank_material():
    member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )
    member.Material = "A513 Type 5 DOM"

    assert members_with_material(
        [member],
        "   ",
    ) == []


# ---------------------------------------------------------
# Available materials
# ---------------------------------------------------------


def test_available_materials_returns_unique_materials():
    member_1 = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )
    member_1.Material = "A513 Type 5 DOM"

    member_2 = FakeMember(
        "M002",
        "1.750 x .120 DOM",
    )
    member_2.Material = "4130 Chromoly"

    member_3 = FakeMember(
        "M003",
        "1.000 x .065 DOM",
    )
    member_3.Material = "A513 Type 5 DOM"

    assert available_materials(
        [
            member_1,
            member_2,
            member_3,
        ]
    ) == [
        "A513 Type 5 DOM",
        "4130 Chromoly",
    ]


def test_available_materials_ignores_empty_materials():
    member_1 = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )
    member_1.Material = ""

    member_2 = FakeMember(
        "M002",
        "1.750 x .120 DOM",
    )
    member_2.Material = "A513 Type 5 DOM"

    assert available_materials(
        [
            member_1,
            member_2,
        ]
    ) == [
        "A513 Type 5 DOM",
    ]


# ---------------------------------------------------------
# Length-range filtering
# ---------------------------------------------------------


def test_members_with_length_range_returns_matches():
    member_1 = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )
    member_1.MemberLength = 500.0

    member_2 = FakeMember(
        "M002",
        "1.750 x .120 DOM",
    )
    member_2.MemberLength = 800.0

    member_3 = FakeMember(
        "M003",
        "1.750 x .120 DOM",
    )
    member_3.MemberLength = 1000.0

    member_4 = FakeMember(
        "M004",
        "1.750 x .120 DOM",
    )
    member_4.MemberLength = 1500.0

    result = members_with_length_range(
        [
            member_1,
            member_2,
            member_3,
            member_4,
        ],
        750.0,
        1100.0,
    )

    assert result == [
        member_2,
        member_3,
    ]


def test_members_with_length_range_includes_boundaries():
    member_1 = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )
    member_1.MemberLength = 750.0

    member_2 = FakeMember(
        "M002",
        "1.750 x .120 DOM",
    )
    member_2.MemberLength = 1100.0

    assert members_with_length_range(
        [
            member_1,
            member_2,
        ],
        750.0,
        1100.0,
    ) == [
        member_1,
        member_2,
    ]


def test_members_with_length_range_accepts_reversed_range():
    member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )
    member.MemberLength = 900.0

    assert members_with_length_range(
        [member],
        1100.0,
        750.0,
    ) == [member]


def test_members_with_length_range_ignores_missing_length():
    member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
    )

    assert members_with_length_range(
        [member],
        0.0,
        1000.0,
    ) == []

class FakeMember:
    def __init__(
        self,
        member_id,
        profile,
        member_name="",
    ):
        self.MemberID = member_id
        self.TubeProfile = profile
        self.MemberName = member_name


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


def test_members_with_name_prefix_returns_matches():
    member_1 = FakeMember(
        "M001",
        "1.750 x .120 DOM",
        "Crossmember 1",
    )

    member_2 = FakeMember(
        "M002",
        "1.750 x .120 DOM",
        "Roof Bar 1",
    )

    member_3 = FakeMember(
        "M003",
        "1.750 x .120 DOM",
        "Crossmember 2",
    )

    result = members_with_name_prefix(
        [
            member_1,
            member_2,
            member_3,
        ],
        "Crossmember",
    )

    assert result == [
        member_1,
        member_3,
    ]


def test_members_with_name_prefix_is_case_insensitive():
    member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
        "Crossmember 1",
    )

    assert (
        members_with_name_prefix(
            [member],
            "crossmember",
        )
        == [member]
    )


def test_members_with_name_prefix_trims_input():
    member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
        "Roof Bar 1",
    )

    assert (
        members_with_name_prefix(
            [member],
            "   Roof Bar   ",
        )
        == [member]
    )


def test_members_with_name_prefix_returns_empty_for_blank_prefix():
    member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
        "Crossmember 1",
    )

    assert (
        members_with_name_prefix(
            [member],
            "",
        )
        == []
    )


def test_members_with_name_prefix_returns_empty_for_whitespace_prefix():
    member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
        "Crossmember 1",
    )

    assert (
        members_with_name_prefix(
            [member],
            "     ",
        )
        == []
    )


def test_members_with_name_prefix_ignores_unnamed_members():
    named_member = FakeMember(
        "M001",
        "1.750 x .120 DOM",
        "Crossmember 1",
    )

    unnamed_member = FakeMember(
        "M002",
        "1.750 x .120 DOM",
        "",
    )

    result = members_with_name_prefix(
        [
            unnamed_member,
            named_member,
        ],
        "Crossmember",
    )

    assert result == [
        named_member
    ]


def test_members_with_name_prefix_preserves_order():
    member_7 = FakeMember(
        "M007",
        "1.750 x .120 DOM",
        "Brace Rear",
    )

    member_2 = FakeMember(
        "M002",
        "1.750 x .120 DOM",
        "Brace Front",
    )

    member_5 = FakeMember(
        "M005",
        "1.750 x .120 DOM",
        "Brace Center",
    )

    result = members_with_name_prefix(
        [
            member_7,
            member_2,
            member_5,
        ],
        "Brace",
    )

    assert result == [
        member_7,
        member_2,
        member_5,
    ]


def test_members_with_name_prefix_does_not_modify_input():
    members = [
        FakeMember(
            "M001",
            "1.750 x .120 DOM",
            "Crossmember 1",
        ),
        FakeMember(
            "M002",
            "1.750 x .120 DOM",
            "Roof Bar 1",
        ),
    ]

    original = list(
        members
    )

    members_with_name_prefix(
        members,
        "Crossmember",
    )

    assert members == original
    