"""Tests for persistent ForgeCAD bender tooling storage."""

import sys
import types

from forgecad.fabrication import (
    BendMarkReference,
    BenderLibrary,
    BenderTooling,
)


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad.bender_library_store import (
    STORE_OBJECT_NAME,
    load_bender_library,
    save_bender_library,
)


class FakeGroup:
    def __init__(
        self,
        name,
    ):
        self.Name = name
        self.Label = name
        self.Group = []

    def addObject(
        self,
        obj,
    ):
        if obj not in self.Group:
            self.Group.append(
                obj
            )


class FakeObject:
    def __init__(
        self,
        name,
    ):
        self.Name = name
        self.Label = name
        self._editor_modes = {}

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        if property_type == "App::PropertyStringList":
            setattr(
                self,
                property_name,
                [],
            )
        else:
            setattr(
                self,
                property_name,
                "",
            )

    def setEditorMode(
        self,
        property_name,
        mode,
    ):
        self._editor_modes[
            property_name
        ] = mode


class FakeDocument:
    def __init__(
        self,
    ):
        self.objects = {}
        self.recompute_count = 0

        root = FakeGroup(
            "ForgeCADProject"
        )
        settings = FakeGroup(
            "ForgeCADSettings"
        )

        root.addObject(
            settings
        )

        self.objects[
            root.Name
        ] = root
        self.objects[
            settings.Name
        ] = settings

    def getObject(
        self,
        name,
    ):
        return self.objects.get(
            name
        )

    def addObject(
        self,
        type_name,
        name,
    ):
        if type_name in (
            "App::DocumentObjectGroup",
            "App::DocumentObjectGroupPython",
        ):
            obj = FakeGroup(
                name
            )
        else:
            obj = FakeObject(
                name
            )

        self.objects[
            name
        ] = obj

        return obj

    def recompute(
        self,
    ):
        self.recompute_count += 1


def _library():
    library = BenderLibrary()

    library.add(
        BenderTooling(
            name="100 mm CLR",
            centerline_radius_mm=100.0,
            mark_reference=(
                BendMarkReference.START_TANGENT
            ),
            mark_offset_mm=5.0,
            angle_compensation_degrees=2.0,
        )
    )

    library.add(
        BenderTooling(
            name="150 mm CLR",
            centerline_radius_mm=150.0,
            mark_reference=(
                BendMarkReference.CENTER_OF_BEND
            ),
            mark_offset_mm=-3.0,
            angle_compensation_degrees=1.5,
        )
    )

    library.set_active(
        "150 mm CLR"
    )

    return library


def test_save_and_load_bender_library_round_trip():
    document = FakeDocument()

    save_bender_library(
        document,
        _library(),
    )

    restored = load_bender_library(
        document
    )

    assert restored.names == (
        "100 mm CLR",
        "150 mm CLR",
    )

    assert restored.active_name == "150 mm CLR"

    first = restored.get(
        "100 mm CLR"
    )

    assert first.centerline_radius_mm == 100.0
    assert (
        first.mark_reference
        == BendMarkReference.START_TANGENT
    )
    assert first.mark_offset_mm == 5.0
    assert first.angle_compensation_degrees == 2.0

    second = restored.get(
        "150 mm CLR"
    )

    assert second.centerline_radius_mm == 150.0
    assert (
        second.mark_reference
        == BendMarkReference.CENTER_OF_BEND
    )
    assert second.mark_offset_mm == -3.0
    assert second.angle_compensation_degrees == 1.5


def test_empty_document_loads_empty_library():
    document = FakeDocument()

    library = load_bender_library(
        document
    )

    assert library.names == ()
    assert library.active_name is None


def test_saved_store_lives_under_settings_group():
    document = FakeDocument()

    store = save_bender_library(
        document,
        _library(),
    )

    settings = document.getObject(
        "ForgeCADSettings"
    )

    assert store.Name == STORE_OBJECT_NAME
    assert store in settings.Group


def test_inconsistent_persisted_lists_are_rejected():
    document = FakeDocument()

    store = document.addObject(
        "App::FeaturePython",
        STORE_OBJECT_NAME,
    )

    store.addProperty(
        "App::PropertyStringList",
        "ToolingNames",
        "ForgeCAD Bender Library",
    )
    store.addProperty(
        "App::PropertyStringList",
        "CenterlineRadii",
        "ForgeCAD Bender Library",
    )
    store.addProperty(
        "App::PropertyStringList",
        "MarkReferences",
        "ForgeCAD Bender Library",
    )
    store.addProperty(
        "App::PropertyStringList",
        "MarkOffsets",
        "ForgeCAD Bender Library",
    )
    store.addProperty(
        "App::PropertyStringList",
        "AngleCompensations",
        "ForgeCAD Bender Library",
    )
    store.addProperty(
        "App::PropertyString",
        "ActiveToolingName",
        "ForgeCAD Bender Library",
    )

    store.ToolingNames = [
        "100 mm CLR",
    ]
    store.CenterlineRadii = []
    store.MarkReferences = []
    store.MarkOffsets = []
    store.AngleCompensations = []

    try:
        load_bender_library(
            document
        )
        assert False
    except ValueError as error:
        assert "inconsistent" in str(
            error
        )
