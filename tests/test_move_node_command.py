"""Tests for the ForgeCAD Move Node command."""

import sys
import types
from types import SimpleNamespace


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(
            x
        )
        self.y = float(
            y
        )
        self.z = float(
            z
        )


class FakeQDialog:
    Accepted = 1

    def reject(
        self,
    ):
        return None


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
fake_freecad.Vector = FakeVector
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)
fake_freecad_gui.Selection = SimpleNamespace(
    getSelection=lambda: [],
    clearSelection=lambda: None,
    addSelection=lambda obj: None,
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
    QDialog=FakeQDialog,
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
    move_node as module,
)


class FakeDocument:
    def __init__(
        self,
    ):
        self.recompute_count = 0
        self.events = []

    def recompute(
        self,
    ):
        self.recompute_count += 1
        self.events.append(
            "recompute"
        )

    def openTransaction(
        self,
        name,
    ):
        self.events.append(
            (
                "open",
                name,
            )
        )

    def commitTransaction(
        self,
    ):
        self.events.append(
            "commit"
        )

    def abortTransaction(
        self,
    ):
        self.events.append(
            "abort"
        )


class FakePlacement:
    def __init__(
        self,
        point,
    ):
        self.Base = FakeVector(
            *point
        )


class FakeNode:
    def __init__(
        self,
        point=(
            100.0,
            200.0,
            300.0,
        ),
    ):
        self.NodeID = "N001"
        self.Position = FakeVector(
            *point
        )
        self.Placement = FakePlacement(
            point
        )
        self.Proxy = None


def test_node_detection_requires_expected_properties():
    node = FakeNode()

    assert module.is_forgecad_node(
        node
    )

    assert not module.is_forgecad_node(
        SimpleNamespace()
    )

    assert not module.is_forgecad_node(
        None
    )


def test_node_position_reads_authoritative_placement():
    node = FakeNode()

    node.Position = FakeVector(
        1.0,
        2.0,
        3.0,
    )

    node.Placement.Base = FakeVector(
        10.0,
        20.0,
        30.0,
    )

    result = module.node_position(
        node
    )

    assert (
        result.x,
        result.y,
        result.z,
    ) == (
        10.0,
        20.0,
        30.0,
    )


def test_preview_node_position_moves_and_recomputes_once(
    monkeypatch,
):
    document = FakeDocument()
    node = FakeNode()

    ensured = []

    monkeypatch.setattr(
        module,
        "ensure_node_proxy",
        lambda obj: ensured.append(
            obj
        ),
    )

    result = module.preview_node_position(
        document,
        node,
        500.0,
        -125.0,
        900.0,
    )

    assert result is node

    assert ensured == [
        node
    ]

    assert (
        node.Placement.Base.x,
        node.Placement.Base.y,
        node.Placement.Base.z,
    ) == (
        500.0,
        -125.0,
        900.0,
    )

    assert (
        document.recompute_count
        == 1
    )


def test_move_node_refreshes_joint_topology_after_live_geometry(
    monkeypatch,
):
    document = FakeDocument()
    node = FakeNode()
    events = []

    monkeypatch.setattr(
        module,
        "ensure_node_proxy",
        lambda obj: events.append(
            "ensure-proxy"
        ),
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

    fake_topology_refresh = types.ModuleType(
        "forgecad.adapters.freecad.topology_refresh"
    )

    fake_topology_refresh.refresh_joint_topology = (
        lambda doc: events.append(
            "refresh-joints"
        )
        or (
            (),
            (),
        )
    )

    monkeypatch.setitem(
        sys.modules,
        "forgecad.adapters.freecad.topology_refresh",
        fake_topology_refresh,
    )

    module.move_node(
        document,
        node,
        500.0,
        250.0,
        900.0,
    )

    assert events == [
        "ensure-proxy",
        "recompute",
        "refresh-joints",
        "recompute",
    ]


def test_move_transaction_opens_with_stable_label():
    document = FakeDocument()

    started = (
        module.open_move_transaction(
            document
        )
    )

    assert started

    assert document.events == [
        (
            "open",
            "Move ForgeCAD Node",
        )
    ]


def test_move_transaction_commits_when_started():
    document = FakeDocument()

    module.commit_move_transaction(
        document,
        True,
    )

    assert document.events == [
        "commit"
    ]


def test_move_transaction_does_not_commit_when_not_started():
    document = FakeDocument()

    module.commit_move_transaction(
        document,
        False,
    )

    assert document.events == []


def test_move_transaction_aborts_when_started():
    document = FakeDocument()

    module.abort_move_transaction(
        document,
        True,
    )

    assert document.events == [
        "abort"
    ]


def test_move_transaction_does_not_abort_when_not_started():
    document = FakeDocument()

    module.abort_move_transaction(
        document,
        False,
    )

    assert document.events == []


def test_preview_rejects_missing_document():
    node = FakeNode()

    try:
        module.preview_node_position(
            None,
            node,
            0.0,
            0.0,
            0.0,
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


def test_preview_rejects_non_node_object():
    document = FakeDocument()

    try:
        module.preview_node_position(
            document,
            SimpleNamespace(),
            0.0,
            0.0,
            0.0,
        )
    except ValueError as error:
        assert (
            "not a ForgeCAD node"
            in str(
                error
            )
        )
    else:
        raise AssertionError(
            "Expected invalid node to fail."
        )


def test_command_name_is_stable():
    assert module.COMMAND_NAME == (
        "ForgeCAD_MoveNode"
    )
