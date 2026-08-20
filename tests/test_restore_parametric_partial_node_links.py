"""Tests for restoring partial node links on regenerated members."""

import sys
import types


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class FakeNode:
    def __init__(
        self,
        name,
        point,
    ):
        self.Name = name
        self.NodeID = name

        self.Position = FakeVector(
            *point
        )


class FakeMember:
    def __init__(
        self,
        name,
        start,
        end,
    ):
        self.Name = name
        self.MemberID = name

        self.StartPoint = FakeVector(
            *start
        )

        self.EndPoint = FakeVector(
            *end
        )

        self.StartNode = None
        self.EndNode = None

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        setattr(
            self,
            property_name,
            None,
        )


class FakeGroup:
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
        nodes,
    ):
        self.nodes = list(
            nodes
        )


fake_freecad = sys.modules.get(
    "FreeCAD"
)

if fake_freecad is None:
    fake_freecad = types.ModuleType(
        "FreeCAD"
    )

    sys.modules[
        "FreeCAD"
    ] = fake_freecad

fake_freecad.Vector = FakeVector
fake_freecad.ActiveDocument = None


fake_freecad_gui = sys.modules.get(
    "FreeCADGui"
)

if fake_freecad_gui is None:
    fake_freecad_gui = types.ModuleType(
        "FreeCADGui"
    )

    sys.modules[
        "FreeCADGui"
    ] = fake_freecad_gui

fake_freecad_gui.Selection = (
    types.SimpleNamespace(
        getSelection=lambda: [],
        clearSelection=lambda: None,
    )
)

fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)

fake_freecad_gui.activeDocument = (
    lambda: None
)

fake_freecad_gui.getMainWindow = (
    lambda: None
)


fake_part = sys.modules.get(
    "Part"
)

if fake_part is None:
    fake_part = types.ModuleType(
        "Part"
    )

    sys.modules[
        "Part"
    ] = fake_part


fake_pyside = sys.modules.get(
    "PySide"
)

if fake_pyside is None:
    fake_pyside = types.ModuleType(
        "PySide"
    )

    sys.modules[
        "PySide"
    ] = fake_pyside


class FakeQDialog:
    pass


class FakeMessageBox:
    @staticmethod
    def warning(
        *args,
        **kwargs,
    ):
        return None


fake_pyside.QtGui = (
    types.SimpleNamespace(
        QDialog=FakeQDialog,
        QMessageBox=FakeMessageBox,
    )
)


from forgecad.adapters.freecad.commands import (
    generate_from_selection,
)


def fake_initialize_project_tree(
    document,
):
    return {
        "Nodes": FakeGroup(
            document.nodes
        )
    }


def test_branch_member_restores_only_matching_start_node():
    junction = FakeNode(
        "N001",
        (
            0.0,
            0.0,
            0.0,
        ),
    )

    document = FakeDocument(
        [
            junction,
        ]
    )

    branch = FakeMember(
        "M001",
        start=(
            0.0,
            0.0,
            0.0,
        ),
        end=(
            0.0,
            500.0,
            0.0,
        ),
    )

    original = (
        generate_from_selection.initialize_project_tree
    )

    generate_from_selection.initialize_project_tree = (
        fake_initialize_project_tree
    )

    try:
        generate_from_selection.restore_rendered_member_node_links(
            document,
            [
                branch,
            ],
        )

    finally:
        generate_from_selection.initialize_project_tree = (
            original
        )

    assert branch.StartNode is junction
    assert branch.EndNode is None


def test_branch_member_restores_only_matching_end_node():
    junction = FakeNode(
        "N001",
        (
            0.0,
            0.0,
            0.0,
        ),
    )

    document = FakeDocument(
        [
            junction,
        ]
    )

    branch = FakeMember(
        "M001",
        start=(
            0.0,
            500.0,
            0.0,
        ),
        end=(
            0.0,
            0.0,
            0.0,
        ),
    )

    original = (
        generate_from_selection.initialize_project_tree
    )

    generate_from_selection.initialize_project_tree = (
        fake_initialize_project_tree
    )

    try:
        generate_from_selection.restore_rendered_member_node_links(
            document,
            [
                branch,
            ],
        )

    finally:
        generate_from_selection.initialize_project_tree = (
            original
        )

    assert branch.StartNode is None
    assert branch.EndNode is junction
    