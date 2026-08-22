"""Tests for reusable ForgeCAD orphan-node cleanup."""

import sys
import types
from types import SimpleNamespace


# Minimal FreeCAD runtime stubs for ordinary Python/pytest.
sys.modules[
    "FreeCAD"
] = types.ModuleType(
    "FreeCAD"
)

sys.modules[
    "FreeCADGui"
] = types.ModuleType(
    "FreeCADGui"
)

sys.modules[
    "Part"
] = types.ModuleType(
    "Part"
)


from forgecad.adapters.freecad.node_cleanup import (
    node_is_referenced,
    object_references_node,
    remove_node_if_unused,
)


class FakeGroup:
    def __init__(
        self,
        objects=(),
    ):
        self.Group = list(
            objects
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
        objects=(),
    ):
        self.Objects = list(
            objects
        )

    def removeObject(
        self,
        name,
    ):
        self.Objects = [
            obj
            for obj in self.Objects
            if getattr(
                obj,
                "Name",
                None,
            )
            != name
        ]


def test_straight_member_start_link_counts_as_reference():
    node = SimpleNamespace(
        Name="Node001"
    )

    member = SimpleNamespace(
        StartNode=node,
        EndNode=None,
    )

    assert object_references_node(
        member,
        node,
    )


def test_bent_tube_end_link_counts_as_reference():
    node = SimpleNamespace(
        Name="Node001"
    )

    bent_tube = SimpleNamespace(
        StartNode=None,
        EndNode=node,
    )

    document = FakeDocument(
        (
            node,
            bent_tube,
        )
    )

    assert node_is_referenced(
        document,
        node,
    )


def test_unused_node_is_removed_from_group_and_document():
    node = SimpleNamespace(
        Name="Node001"
    )

    group = FakeGroup(
        (
            node,
        )
    )

    document = FakeDocument(
        (
            group,
            node,
        )
    )

    assert remove_node_if_unused(
        document,
        node,
    )

    assert node not in group.Group
    assert node not in document.Objects


def test_shared_node_is_preserved():
    node = SimpleNamespace(
        Name="Node001"
    )

    member = SimpleNamespace(
        StartNode=node,
        EndNode=None,
    )

    group = FakeGroup(
        (
            node,
        )
    )

    document = FakeDocument(
        (
            group,
            node,
            member,
        )
    )

    assert not remove_node_if_unused(
        document,
        node,
    )

    assert node in group.Group
    assert node in document.Objects


def test_none_node_is_safe_no_op():
    document = FakeDocument()

    assert not remove_node_if_unused(
        document,
        None,
    )
