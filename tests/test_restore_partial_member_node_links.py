"""Tests for restoring partial node links on regenerated members."""

import importlib
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


class FakeQDialog:
    pass


class FakeMessageBox:
    @staticmethod
    def warning(
        *args,
        **kwargs,
    ):
        return None


def import_generate_module():
    """
    Import generate_from_selection with temporary FreeCAD/PySide doubles.

    The original external modules are restored afterward so this test
    does not pollute the rest of pytest collection.
    """

    module_names = (
        "FreeCAD",
        "FreeCADGui",
        "Part",
        "PySide",
    )

    previous_modules = {
        name: sys.modules.get(
            name
        )
        for name in module_names
    }

    fake_freecad = types.ModuleType(
        "FreeCAD"
    )

    fake_freecad.Vector = (
        FakeVector
    )

    fake_freecad.ActiveDocument = None

    fake_freecad_gui = types.ModuleType(
        "FreeCADGui"
    )

    fake_freecad_gui.Selection = (
        types.SimpleNamespace(
            getSelection=lambda: [],
            clearSelection=lambda: None,
        )
    )

    fake_freecad_gui.getMainWindow = (
        lambda: None
    )

    fake_freecad_gui.activeDocument = (
        lambda: None
    )

    fake_part = types.ModuleType(
        "Part"
    )

    fake_pyside = types.ModuleType(
        "PySide"
    )

    fake_pyside.QtGui = (
        types.SimpleNamespace(
            QDialog=FakeQDialog,
            QMessageBox=FakeMessageBox,
        )
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

    sys.modules[
        "PySide"
    ] = fake_pyside

    try:
        module = importlib.import_module(
            "forgecad.adapters.freecad.commands.generate_from_selection"
        )

    finally:
        for (
            module_name,
            previous_module,
        ) in previous_modules.items():
            if previous_module is None:
                sys.modules.pop(
                    module_name,
                    None,
                )
            else:
                sys.modules[
                    module_name
                ] = previous_module

    return module


generate_from_selection = (
    import_generate_module()
)

restore_rendered_member_node_links = (
    generate_from_selection.restore_rendered_member_node_links
)


class FakeNode:
    def __init__(
        self,
        node_id,
        point,
    ):
        self.NodeID = node_id

        self.Position = FakeVector(
            *point
        )


class FakeNodeGroup:
    def __init__(
        self,
        nodes,
    ):
        self.Group = list(
            nodes
        )


class FakeDocument:
    def __init__(
        self,
        nodes,
    ):
        self.nodes_group = FakeNodeGroup(
            nodes
        )


class FakeMember:
    def __init__(
        self,
        member_id,
        start,
        end,
    ):
        self.MemberID = member_id

        self.StartPoint = FakeVector(
            *start
        )

        self.EndPoint = FakeVector(
            *end
        )

        self.added_properties = []

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        self.added_properties.append(
            (
                property_type,
                property_name,
                group,
            )
        )

        setattr(
            self,
            property_name,
            None,
        )


def fake_initialize_project_tree(
    document,
):
    """
    Return only the project-tree portion required by _node_lookup().

    This keeps the test focused on node-link restoration rather than
    recreating FreeCAD's complete document/group API.
    """

    return {
        "Nodes": document.nodes_group,
    }


generate_from_selection.initialize_project_tree = (
    fake_initialize_project_tree
)


def test_branch_member_restores_only_junction_start_node():
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

    restore_rendered_member_node_links(
        document,
        [
            branch,
        ],
    )

    assert (
        branch.StartNode
        is junction
    )

    assert (
        branch.EndNode
        is None
    )


def test_branch_member_restores_only_junction_end_node():
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

    restore_rendered_member_node_links(
        document,
        [
            branch,
        ],
    )

    assert (
        branch.StartNode
        is None
    )

    assert (
        branch.EndNode
        is junction
    )
    