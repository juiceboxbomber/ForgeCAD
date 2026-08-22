"""Tests for the ForgeCAD Delete Member command."""

import sys
import types
from types import SimpleNamespace


class FakeQMessageBox:
    @staticmethod
    def warning(*args, **kwargs):
        return None


fake_freecad = types.ModuleType("FreeCAD")
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType("FreeCADGui")
fake_freecad_gui.Selection = SimpleNamespace(
    getSelection=lambda: [],
    clearSelection=lambda: None,
)
fake_freecad_gui.addCommand = lambda *args, **kwargs: None
fake_freecad_gui.getMainWindow = lambda: None

fake_pyside = types.ModuleType("PySide")
fake_pyside.QtGui = SimpleNamespace(
    QMessageBox=FakeQMessageBox,
)

fake_part = types.ModuleType("Part")

sys.modules["FreeCAD"] = fake_freecad
sys.modules["FreeCADGui"] = fake_freecad_gui
sys.modules["PySide"] = fake_pyside
sys.modules["Part"] = fake_part


from forgecad.adapters.freecad.commands import delete_member as module


class FakeDocument:
    def __init__(self):
        self.recompute_count = 0

    def recompute(self):
        self.recompute_count += 1


def make_member(
    start_node=None,
    end_node=None,
):
    return SimpleNamespace(
        Name="Member001",
        MemberID="M001",
        SourceLayoutID="L001",
        StartNode=start_node,
        EndNode=end_node,
    )


def test_member_detection_requires_member_metadata():
    assert module.is_forgecad_member(
        make_member()
    )
    assert not module.is_forgecad_member(
        SimpleNamespace(MemberID="M001")
    )
    assert not module.is_forgecad_member(None)


def test_endpoint_nodes_returns_unique_linked_nodes():
    first = object()
    second = object()

    member = make_member(
        start_node=first,
        end_node=second,
    )

    assert module.endpoint_nodes(member) == (
        first,
        second,
    )

    member.EndNode = first

    assert module.endpoint_nodes(member) == (
        first,
    )


def test_delete_member_uses_safe_cleanup_order(
    monkeypatch,
):
    document = FakeDocument()
    start_node = object()
    end_node = object()

    member = make_member(
        start_node=start_node,
        end_node=end_node,
    )

    events = []

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda doc, obj: events.append(
            "remove-member"
        ) or True,
    )

    monkeypatch.setattr(
        module,
        "remove_node_if_unused",
        lambda doc, node: events.append(
            ("remove-node", node)
        ) or True,
    )

    monkeypatch.setattr(
        module,
        "refresh_joint_topology",
        lambda doc: events.append(
            "refresh-joints"
        ) or ((), ()),
    )

    monkeypatch.setattr(
        module,
        "refresh_fabrication_for_document",
        lambda doc: events.append(
            "refresh-fabrication"
        ) or (),
    )

    original_recompute = document.recompute

    def tracked_recompute():
        events.append("recompute")
        original_recompute()

    document.recompute = tracked_recompute

    assert module.delete_member(
        document,
        member,
    )

    assert events == [
        "remove-member",
        ("remove-node", start_node),
        ("remove-node", end_node),
        "recompute",
        "refresh-joints",
        "refresh-fabrication",
        "recompute",
    ]


def test_delete_member_rejects_missing_document():
    try:
        module.delete_member(
            None,
            make_member(),
        )
    except ValueError as error:
        assert "document" in str(error).lower()
    else:
        raise AssertionError(
            "Expected missing document to fail."
        )


def test_delete_member_rejects_non_member():
    try:
        module.delete_member(
            FakeDocument(),
            SimpleNamespace(),
        )
    except ValueError as error:
        assert "not a ForgeCAD straight member" in str(error)
    else:
        raise AssertionError(
            "Expected invalid member to fail."
        )


def test_failed_member_removal_stops_cleanup(
    monkeypatch,
):
    document = FakeDocument()
    member = make_member(
        start_node=object(),
        end_node=object(),
    )
    node_cleanup_calls = []

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda doc, obj: False,
    )

    monkeypatch.setattr(
        module,
        "remove_node_if_unused",
        lambda doc, node: node_cleanup_calls.append(
            node
        ),
    )

    try:
        module.delete_member(
            document,
            member,
        )
    except RuntimeError as error:
        assert "could not remove" in str(error)
    else:
        raise AssertionError(
            "Expected failed removal to raise."
        )

    assert node_cleanup_calls == []


def test_command_name_is_stable():
    assert module.COMMAND_NAME == "ForgeCAD_DeleteMember"
