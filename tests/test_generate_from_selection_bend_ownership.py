"""Tests for excluding bend-owned layout lines during frame regeneration."""

import sys
import types


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.ActiveDocument = None

sys.modules[
    "FreeCAD"
] = fake_freecad


fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_freecad_gui.Selection = types.SimpleNamespace(
    getSelection=lambda: [],
)

sys.modules[
    "FreeCADGui"
] = fake_freecad_gui


class FakeDialog:
    pass


fake_pyside = types.ModuleType(
    "PySide"
)

fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=FakeDialog,
    QMessageBox=object,
)

sys.modules[
    "PySide"
] = fake_pyside


from forgecad.adapters.freecad.commands import (
    generate_from_selection,
)


class FakeLayoutObject:
    pass


class FakeBentTube:
    def __init__(
        self,
        source_layout_lines=(),
    ):
        self.SourceLayoutLines = list(
            source_layout_lines
        )


class FakeGroup:
    def __init__(
        self,
        objects=(),
    ):
        self.Group = list(
            objects
        )


class FakeDocument:
    def __init__(
        self,
        bent_tubes=(),
    ):
        self.bent_tubes_group = FakeGroup(
            bent_tubes
        )

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADBentTubes":
            return self.bent_tubes_group

        return None


def test_bend_owned_layout_lines_are_excluded_from_regeneration():
    first = FakeLayoutObject()
    second = FakeLayoutObject()
    third = FakeLayoutObject()

    bend = FakeBentTube(
        (
            first,
            second,
        )
    )

    document = FakeDocument(
        (
            bend,
        )
    )

    result = (
        generate_from_selection
        .unconsumed_layout_objects(
            document,
            [
                first,
                second,
                third,
            ],
        )
    )

    assert result == [
        third,
    ]


def test_layout_lines_without_bend_ownership_remain_available():
    first = FakeLayoutObject()
    second = FakeLayoutObject()

    document = FakeDocument()

    result = (
        generate_from_selection
        .unconsumed_layout_objects(
            document,
            [
                first,
                second,
            ],
        )
    )

    assert result == [
        first,
        second,
    ]


def test_all_layout_lines_may_be_consumed_by_bends():
    first = FakeLayoutObject()
    second = FakeLayoutObject()

    bend = FakeBentTube(
        (
            first,
            second,
        )
    )

    document = FakeDocument(
        (
            bend,
        )
    )

    result = (
        generate_from_selection
        .unconsumed_layout_objects(
            document,
            [
                first,
                second,
            ],
        )
    )

    assert result == []
    