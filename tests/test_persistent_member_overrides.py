"""Tests for persistent member profile override behavior."""

import importlib
import sys
import types


# ----------------------------------------------------------------------
# Minimal FreeCAD stubs
#
# These allow us to import the FreeCAD adapter modules during normal
# pytest runs without requiring FreeCAD itself to be installed.
# ----------------------------------------------------------------------

freecad_stub = types.ModuleType("FreeCAD")
part_stub = types.ModuleType("Part")
freecad_gui_stub = types.ModuleType("FreeCADGui")

pyside_stub = types.ModuleType("PySide")
qtgui_stub = types.ModuleType("QtGui")


class FakeQDialog:
    pass


qtgui_stub.QDialog = FakeQDialog
pyside_stub.QtGui = qtgui_stub


class FakeSelection:
    @staticmethod
    def getSelection():
        return []

    @staticmethod
    def clearSelection():
        pass


freecad_gui_stub.Selection = FakeSelection()


sys.modules.setdefault(
    "FreeCAD",
    freecad_stub,
)

sys.modules.setdefault(
    "Part",
    part_stub,
)

sys.modules.setdefault(
    "FreeCADGui",
    freecad_gui_stub,
)

sys.modules.setdefault(
    "PySide",
    pyside_stub,
)

sys.modules.setdefault(
    "PySide.QtGui",
    qtgui_stub,
)


# Import after installing the stubs.
generate_module = importlib.import_module(
    "forgecad.adapters.freecad.commands.generate_from_selection"
)

member_object_module = importlib.import_module(
    "forgecad.adapters.freecad.member_object"
)


profile_overrides_for_objects = (
    generate_module.profile_overrides_for_objects
)

apply_profile_overrides = (
    generate_module.apply_profile_overrides
)

ensure_profile_override_property = (
    member_object_module.ensure_profile_override_property
)

find_source_layout_object = (
    member_object_module.find_source_layout_object
)


# ----------------------------------------------------------------------
# Fake FreeCAD-like objects
# ----------------------------------------------------------------------


class FakeLayoutObject:
    """Minimal object representing a ForgeCAD layout line."""

    def __init__(
        self,
        layout_id,
        override=None,
    ):
        self.LayoutID = layout_id

        if override is not None:
            self.TubeProfileOverride = override

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        setattr(
            self,
            property_name,
            "",
        )


class FakeGroup:
    """Minimal FreeCAD document group."""

    def __init__(
        self,
        objects=None,
    ):
        self.Group = list(
            objects or []
        )


class FakeDocument:
    """Minimal document object lookup."""

    def __init__(
        self,
        layout_objects=None,
    ):
        self.layout_group = FakeGroup(
            layout_objects
        )

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADLayout":
            return self.layout_group

        return None


class FakeMemberObject:
    """Minimal generated member."""

    def __init__(
        self,
        source_layout_id="",
        document=None,
    ):
        self.SourceLayoutID = (
            source_layout_id
        )

        self.Document = document

        self.TubeProfile = ""


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------


def test_no_override_returns_empty_string():
    """Untouched layout lines should have no profile override."""

    layout = FakeLayoutObject(
        layout_id="layout-001"
    )

    overrides = (
        profile_overrides_for_objects(
            [layout]
        )
    )

    assert overrides == [""]


def test_valid_override_is_returned():
    """Valid ForgeCAD profile names should survive lookup."""

    layout = FakeLayoutObject(
        layout_id="layout-001",
        override="1.000 x .065 DOM",
    )

    overrides = (
        profile_overrides_for_objects(
            [layout]
        )
    )

    assert overrides == [
        "1.000 x .065 DOM"
    ]


def test_invalid_override_is_ignored():
    """Unknown profile names must not be restored."""

    layout = FakeLayoutObject(
        layout_id="layout-001",
        override="Imaginary Tube Size",
    )

    overrides = (
        profile_overrides_for_objects(
            [layout]
        )
    )

    assert overrides == [""]


def test_multiple_overrides_preserve_layout_order():
    """Overrides must remain aligned with their source layout objects."""

    layouts = [
        FakeLayoutObject(
            "layout-001",
        ),
        FakeLayoutObject(
            "layout-002",
            "1.000 x .065 DOM",
        ),
        FakeLayoutObject(
            "layout-003",
            "1.250 x .095 DOM",
        ),
    ]

    overrides = (
        profile_overrides_for_objects(
            layouts
        )
    )

    assert overrides == [
        "",
        "1.000 x .065 DOM",
        "1.250 x .095 DOM",
    ]


def test_apply_profile_overrides_updates_only_overridden_members():
    """Only members with stored overrides should be changed."""

    member_1 = FakeMemberObject()
    member_1.TubeProfile = (
        "1.750 x .120 DOM"
    )

    member_2 = FakeMemberObject()
    member_2.TubeProfile = (
        "1.750 x .120 DOM"
    )

    member_3 = FakeMemberObject()
    member_3.TubeProfile = (
        "1.750 x .120 DOM"
    )

    apply_profile_overrides(
        [
            member_1,
            member_2,
            member_3,
        ],
        [
            "",
            "1.000 x .065 DOM",
            "1.250 x .095 DOM",
        ],
    )

    assert (
        member_1.TubeProfile
        == "1.750 x .120 DOM"
    )

    assert (
        member_2.TubeProfile
        == "1.000 x .065 DOM"
    )

    assert (
        member_3.TubeProfile
        == "1.250 x .095 DOM"
    )


def test_override_count_must_match_member_count():
    """Misaligned member and override lists should fail loudly."""

    member = FakeMemberObject()

    try:
        apply_profile_overrides(
            [member],
            [
                "1.000 x .065 DOM",
                "1.250 x .095 DOM",
            ],
        )
    except ValueError as error:
        assert (
            "Profile override count"
            in str(error)
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_override_property_is_created_when_missing():
    """Layout lines should gain persistent override storage."""

    layout = FakeLayoutObject(
        layout_id="layout-001"
    )

    assert not hasattr(
        layout,
        "TubeProfileOverride",
    )

    result = (
        ensure_profile_override_property(
            layout
        )
    )

    assert result is layout

    assert hasattr(
        layout,
        "TubeProfileOverride",
    )

    assert (
        layout.TubeProfileOverride
        == ""
    )


def test_existing_override_property_is_preserved():
    """Creating override storage must not erase an existing value."""

    layout = FakeLayoutObject(
        layout_id="layout-001",
        override="1.000 x .065 DOM",
    )

    ensure_profile_override_property(
        layout
    )

    assert (
        layout.TubeProfileOverride
        == "1.000 x .065 DOM"
    )


def test_member_finds_its_source_layout_by_stable_id():
    """Generated members should resolve their owning layout by UUID."""

    layout_1 = FakeLayoutObject(
        "layout-001"
    )

    layout_2 = FakeLayoutObject(
        "layout-002"
    )

    document = FakeDocument(
        [
            layout_1,
            layout_2,
        ]
    )

    member = FakeMemberObject(
        source_layout_id="layout-002",
        document=document,
    )

    result = find_source_layout_object(
        member
    )

    assert result is layout_2


def test_member_with_unknown_source_id_returns_none():
    """A stale SourceLayoutID must not match the wrong layout."""

    layout = FakeLayoutObject(
        "layout-001"
    )

    document = FakeDocument(
        [layout]
    )

    member = FakeMemberObject(
        source_layout_id="missing-layout",
        document=document,
    )

    result = find_source_layout_object(
        member
    )

    assert result is None
    