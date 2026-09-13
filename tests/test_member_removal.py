"""Tests for safe ForgeCAD member removal."""

import sys
import types
from types import SimpleNamespace


sys.modules["FreeCAD"] = types.ModuleType("FreeCAD")
sys.modules["FreeCADGui"] = types.ModuleType("FreeCADGui")
sys.modules["Part"] = types.ModuleType("Part")


from forgecad.adapters.freecad.member_removal import (
    layout_object_for_id,
    remove_member_and_unused_layout,
)


class FakeGroup:
    def __init__(self, objects=None):
        self.Group = list(objects or [])

    def removeObject(self, obj):
        if obj in self.Group:
            self.Group.remove(obj)


class FakeDocument:
    def __init__(
        self,
        frame_members=None,
        layouts=None,
        nodes=None,
    ):
        self.frame_group = FakeGroup(frame_members)
        self.layout_group = FakeGroup(layouts)
        self.nodes_group = FakeGroup(nodes)

        self.groups = {
            "ForgeCADFrame": self.frame_group,
            "ForgeCADLayout": self.layout_group,
            "ForgeCADNodes": self.nodes_group,
        }

        self.removed_names = []
        self.recompute_count = 0

    def getObject(self, name):
        return self.groups.get(name)

    def removeObject(self, name):
        self.removed_names.append(name)

    def recompute(self):
        self.recompute_count += 1


def member(name, member_id, layout_id):
    return SimpleNamespace(
        Name=name,
        MemberID=member_id,
        SourceLayoutID=layout_id,
    )


def layout(name, layout_id):
    return SimpleNamespace(
        Name=name,
        LayoutID=layout_id,
    )


def test_layout_object_is_found_by_id():
    first = layout("Layout001", "L001")
    second = layout("Layout002", "L002")

    document = FakeDocument(
        layouts=[
            first,
            second,
        ]
    )

    assert (
        layout_object_for_id(
            document,
            "L002",
        )
        is second
    )


def test_removing_member_removes_unused_source_layout():
    source_layout = layout(
        "Layout001",
        "L001",
    )

    source_member = member(
        "Member001",
        "M001",
        "L001",
    )

    document = FakeDocument(
        frame_members=[
            source_member,
        ],
        layouts=[
            source_layout,
        ],
    )

    result = remove_member_and_unused_layout(
        document,
        source_member,
    )

    assert result
    assert source_member not in document.frame_group.Group
    assert source_layout not in document.layout_group.Group
    assert "Member001" in document.removed_names
    assert "Layout001" in document.removed_names


def test_shared_layout_is_not_removed():
    source_layout = layout(
        "Layout001",
        "L001",
    )

    first = member(
        "Member001",
        "M001",
        "L001",
    )

    second = member(
        "Member002",
        "M002",
        "L001",
    )

    document = FakeDocument(
        frame_members=[
            first,
            second,
        ],
        layouts=[
            source_layout,
        ],
    )

    remove_member_and_unused_layout(
        document,
        first,
    )

    assert source_layout in document.layout_group.Group
    assert "Layout001" not in document.removed_names


def test_member_removal_does_not_remove_nodes():
    source_layout = layout(
        "Layout001",
        "L001",
    )

    source_member = member(
        "Member001",
        "M001",
        "L001",
    )

    node_a = SimpleNamespace(
        Name="Node001"
    )

    node_b = SimpleNamespace(
        Name="Node002"
    )

    document = FakeDocument(
        frame_members=[
            source_member,
        ],
        layouts=[
            source_layout,
        ],
        nodes=[
            node_a,
            node_b,
        ],
    )

    remove_member_and_unused_layout(
        document,
        source_member,
    )

    assert document.nodes_group.Group == [
        node_a,
        node_b,
    ]

    assert "Node001" not in document.removed_names
    assert "Node002" not in document.removed_names


def test_removal_recomputes_document():
    source_member = member(
        "Member001",
        "M001",
        "",
    )

    document = FakeDocument(
        frame_members=[
            source_member,
        ]
    )

    remove_member_and_unused_layout(
        document,
        source_member,
    )

    assert document.recompute_count == 1


def test_none_member_does_nothing():
    document = FakeDocument()

    assert not remove_member_and_unused_layout(
        document,
        None,
    )

    assert document.removed_names == []
