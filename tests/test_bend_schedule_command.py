"""Tests for ForgeCAD Bend Schedule command helpers."""

import sys
import types

from forgecad.fabrication import (
    BenderLibrary,
    BenderTooling,
)


fake_freecad = types.ModuleType("FreeCAD")
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType("FreeCADGui")
fake_part = types.ModuleType("Part")

fake_freecad_gui.Selection = types.SimpleNamespace(
    getSelection=lambda: []
)

sys.modules["FreeCAD"] = fake_freecad
sys.modules["FreeCADGui"] = fake_freecad_gui
sys.modules["Part"] = fake_part

fake_pyside = types.ModuleType("PySide")
fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=object,
)

sys.modules["PySide"] = fake_pyside


from forgecad.adapters.freecad.commands import bend_schedule as command


class FakeProxy:
    def __init__(self, tube):
        self.tube = tube

    def _tube_from_properties(self, obj):
        return self.tube


class FakeObject:
    def __init__(self, tube=None, tooling_name=""):
        self.Proxy = (
            FakeProxy(tube)
            if tube is not None
            else None
        )
        self.BenderTooling = tooling_name
        self.TubeName = "Main Hoop"
        self.Label = "Main Hoop"


def test_selected_bent_tube_requires_single_selection(monkeypatch):
    monkeypatch.setattr(
        command.FreeCADGui.Selection,
        "getSelection",
        lambda: [],
    )

    try:
        command.selected_bent_tube_object()
        assert False
    except ValueError as error:
        assert "exactly one" in str(error)


def test_tooling_for_object_returns_none_when_unassigned(monkeypatch):
    obj = FakeObject(
        tube=object(),
        tooling_name="",
    )

    assert command.tooling_for_object(
        object(),
        obj,
    ) is None


def test_tooling_for_object_resolves_persisted_tooling(monkeypatch):
    library = BenderLibrary()

    tooling = BenderTooling(
        name="100 mm CLR Die",
        centerline_radius_mm=100.0,
    )
    library.add(tooling)

    monkeypatch.setattr(
        command,
        "load_bender_library",
        lambda document: library,
    )

    obj = FakeObject(
        tube=object(),
        tooling_name="100 mm CLR Die",
    )

    assert command.tooling_for_object(
        object(),
        obj,
    ) is tooling
