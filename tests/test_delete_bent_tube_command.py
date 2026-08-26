"""Tests for the ForgeCAD Delete Bent Tube command."""

import sys
import types
from types import SimpleNamespace


class FakeQMessageBox:
    @staticmethod
    def warning(
        *args,
        **kwargs,
    ):
        return None


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)
fake_freecad_gui.Selection = SimpleNamespace(
    getSelection=lambda: [],
    clearSelection=lambda: None,
)
fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)
fake_freecad_gui.getMainWindow = (
    lambda: None
)

fake_pyside = types.ModuleType(
    "PySide"
)
fake_pyside.QtGui = SimpleNamespace(
    QMessageBox=FakeQMessageBox,
)

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


from forgecad.adapters.freecad.commands import (
    delete_bent_tube as module,
)


class FakeGroup:
    def __init__(
        self,
        objects=None,
    ):
        self.Group = list(
            objects
            or []
        )

    def removeObject(
        self,
        obj,
    ):
        if obj in self.Group:
            self.Group.remove(
                obj
            )


class FakeDocument:
    def __init__(
        self,
        bent_tubes=None,
    ):
        self.bent_tubes_group = (
            FakeGroup(
                bent_tubes
            )
        )

        self.removed_names = []
        self.recompute_count = 0

    def getObject(
        self,
        name,
    ):
        if (
            name
            == "ForgeCADBentTubes"
        ):
            return (
                self.bent_tubes_group
            )

        return None

    def removeObject(
        self,
        name,
    ):
        self.removed_names.append(
            name
        )

    def recompute(
        self,
    ):
        self.recompute_count += 1


def make_bent_tube(
    start_node=None,
    end_node=None,
):
    return SimpleNamespace(
        Name="ForgeCADBentTube001",
        StartNode=start_node,
        EndNode=end_node,
    )


def test_bent_tube_detection_uses_bent_tubes_group():
    tube = make_bent_tube()

    document = FakeDocument(
        bent_tubes=[
            tube,
        ]
    )

    assert module.is_forgecad_bent_tube(
        document,
        tube,
    )

    assert not module.is_forgecad_bent_tube(
        document,
        SimpleNamespace(),
    )


def test_endpoint_nodes_returns_unique_linked_nodes():
    first = object()
    second = object()

    tube = make_bent_tube(
        start_node=first,
        end_node=second,
    )

    assert module.endpoint_nodes(
        tube
    ) == (
        first,
        second,
    )

    tube.EndNode = first

    assert module.endpoint_nodes(
        tube
    ) == (
        first,
    )


def test_delete_bent_tube_uses_safe_cleanup_order(
    monkeypatch,
):
    start_node = object()
    end_node = object()

    tube = make_bent_tube(
        start_node=start_node,
        end_node=end_node,
    )

    document = FakeDocument(
        bent_tubes=[
            tube,
        ]
    )

    events = []

    monkeypatch.setattr(
        module,
        "remove_node_if_unused",
        lambda doc, node: (
            events.append(
                (
                    "remove-node",
                    node,
                )
            )
            or True
        ),
    )

    monkeypatch.setattr(
        module,
        "refresh_joint_topology",
        lambda doc: (
            events.append(
                "refresh-joints"
            )
            or (
                (),
                (),
            )
        ),
    )

    monkeypatch.setattr(
        module,
        "refresh_fabrication_for_document",
        lambda doc: (
            events.append(
                "refresh-fabrication"
            )
            or ()
        ),
    )

    original_remove = (
        document.removeObject
    )

    def tracked_remove(
        name,
    ):
        events.append(
            (
                "remove-object",
                name,
            )
        )

        original_remove(
            name
        )

    document.removeObject = (
        tracked_remove
    )

    original_recompute = (
        document.recompute
    )

    def tracked_recompute():
        events.append(
            "recompute"
        )

        original_recompute()

    document.recompute = (
        tracked_recompute
    )

    assert module.delete_bent_tube(
        document,
        tube,
    )

    assert tube not in (
        document.bent_tubes_group.Group
    )

    assert events == [
        (
            "remove-object",
            "ForgeCADBentTube001",
        ),
        (
            "remove-node",
            start_node,
        ),
        (
            "remove-node",
            end_node,
        ),
        "recompute",
        "refresh-joints",
        "refresh-fabrication",
        "recompute",
    ]


def test_delete_bent_tube_rejects_missing_document():
    try:
        module.delete_bent_tube(
            None,
            make_bent_tube(),
        )
    except ValueError as error:
        assert (
            "document"
            in str(
                error
            ).lower()
        )
    else:
        raise AssertionError(
            "Expected missing document to fail."
        )


def test_delete_bent_tube_rejects_non_bent_tube():
    document = FakeDocument()

    try:
        module.delete_bent_tube(
            document,
            make_bent_tube(),
        )
    except ValueError as error:
        assert (
            "not a ForgeCAD bent tube"
            in str(
                error
            )
        )
    else:
        raise AssertionError(
            "Expected invalid bent tube to fail."
        )


def test_command_name_is_stable():
    assert module.COMMAND_NAME == (
        "ForgeCAD_DeleteBentTube"
    )
