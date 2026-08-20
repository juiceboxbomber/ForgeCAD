"""Tests for the ForgeCAD fabrication-sheet export command."""

import sys
import types

from forgecad.fabrication import (
    Bend,
    BenderLibrary,
    BenderTooling,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)
fake_part = types.ModuleType(
    "Part"
)

fake_freecad_gui.Selection = types.SimpleNamespace(
    getSelection=lambda: []
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "FreeCADGui"
] = fake_freecad_gui
sys.modules[
    "Part"
] = fake_part

fake_pyside = types.ModuleType(
    "PySide"
)
fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=object,
)

sys.modules[
    "PySide"
] = fake_pyside


from forgecad.adapters.freecad.commands import (
    export_bend_fabrication_sheet as command,
)


class FakeProxy:
    def __init__(
        self,
        tube,
    ):
        self.tube = tube

    def _tube_from_properties(
        self,
        obj,
    ):
        return self.tube


class FakeObject:
    def __init__(
        self,
        tube,
        tooling_name="",
    ):
        self.Proxy = FakeProxy(
            tube
        )
        self.BenderTooling = tooling_name
        self.TubeName = "Main Hoop"
        self.Label = "Bent Tube"


def _tube():
    return BentTube(
        straight_runs=(
            StraightRun(
                500.0
            ),
            StraightRun(
                600.0
            ),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
                rotation_degrees=0.0,
            ),
        ),
        profile=TubeProfile(
            outside_diameter=44.45,
            wall_thickness=3.048,
        ),
        material=Material(
            name="A513 Type 5 DOM",
            density=7850.0,
            yield_strength=350.0,
        ),
    )


def test_tube_name_uses_tube_name_property():
    obj = FakeObject(
        _tube()
    )

    assert (
        command.tube_name_for_object(
            obj
        )
        == "Main Hoop"
    )


def test_default_export_name_uses_tube_name():
    obj = FakeObject(
        _tube()
    )

    assert (
        command.default_export_name(
            obj
        )
        == "Main_Hoop_fabrication_sheet.pdf"
    )


def test_default_export_name_sanitizes_characters():
    obj = FakeObject(
        _tube()
    )
    obj.TubeName = "Main/Hoop #1"

    assert (
        command.default_export_name(
            obj
        )
        == "Main_Hoop__1_fabrication_sheet.pdf"
    )


def test_tooling_for_object_returns_none_when_unassigned():
    obj = FakeObject(
        _tube(),
        tooling_name="",
    )

    assert (
        command.tooling_for_object(
            object(),
            obj,
        )
        is None
    )


def test_tooling_for_object_resolves_saved_tooling(
    monkeypatch,
):
    library = BenderLibrary()

    tooling = BenderTooling(
        name="100 mm CLR Die",
        centerline_radius_mm=100.0,
    )

    library.add(
        tooling
    )

    monkeypatch.setattr(
        command,
        "load_bender_library",
        lambda document: library,
    )

    obj = FakeObject(
        _tube(),
        tooling_name="100 mm CLR Die",
    )

    assert (
        command.tooling_for_object(
            object(),
            obj,
        )
        is tooling
    )


def test_fabrication_sheet_for_object_builds_sheet(
    monkeypatch,
):
    obj = FakeObject(
        _tube()
    )

    sheet = (
        command.fabrication_sheet_for_object(
            object(),
            obj,
        )
    )

    assert sheet.tube_name == "Main Hoop"
    assert sheet.bend_count == 1
    assert sheet.material_name == "A513 Type 5 DOM"


def test_write_fabrication_sheet_pdf_creates_file(
    tmp_path,
):
    obj = FakeObject(
        _tube()
    )

    sheet = (
        command.fabrication_sheet_for_object(
            object(),
            obj,
        )
    )

    output = (
        tmp_path
        / "main_hoop.pdf"
    )

    result = (
        command.write_fabrication_sheet_pdf(
            output,
            sheet,
        )
    )

    assert result == output
    assert output.exists()
    assert (
        output.read_bytes()[
            :4
        ]
        == b"%PDF"
    )
