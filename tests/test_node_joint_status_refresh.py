"""Tests for joint-marker refresh after node topology movement."""

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


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.Vector = FakeVector

fake_part = types.ModuleType(
    "Part"
)
fake_part.makeSphere = (
    lambda *args, **kwargs: (
        "sphere",
        args,
    )
)
fake_part.makeLine = (
    lambda start, end: (
        "line",
        start,
        end,
    )
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "Part"
] = fake_part


import forgecad.adapters.freecad.node_object as node_object


class FakePlacement:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.Base = FakeVector(
            x,
            y,
            z,
        )


class FakeNode:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.Position = FakeVector(
            x,
            y,
            z,
        )
        self.Placement = FakePlacement(
            x,
            y,
            z,
        )
        self.X = float(x)
        self.Y = float(y)
        self.Z = float(z)
        self.Shape = None
        self.Proxy = None
        self.Document = None


class FakeLayoutGroup:
    Group = ()


class FakeDocument:
    def __init__(
        self,
    ):
        self.Objects = []

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADLayout":
            return FakeLayoutGroup()

        return None


def test_node_move_rebuilds_joint_status_objects():
    document = FakeDocument()

    node = FakeNode(
        0.0,
        0.0,
        0.0,
    )
    node.Document = document

    calls = []

    original = (
        node_object.rebuild_joint_status_after_topology_change
    )

    node_object.rebuild_joint_status_after_topology_change = (
        lambda current_document: calls.append(
            current_document
        )
    )

    try:
        proxy = node_object.ForgeCADNodeProxy(
            node
        )

        node.Placement.Base = FakeVector(
            100.0,
            200.0,
            300.0,
        )

        proxy.onChanged(
            node,
            "Placement",
        )

    finally:
        node_object.rebuild_joint_status_after_topology_change = (
            original
        )

    assert calls == [
        document
    ]


def test_unchanged_node_does_not_rebuild_joint_status_objects():
    document = FakeDocument()

    node = FakeNode(
        0.0,
        0.0,
        0.0,
    )
    node.Document = document

    calls = []

    original = (
        node_object.rebuild_joint_status_after_topology_change
    )

    node_object.rebuild_joint_status_after_topology_change = (
        lambda current_document: calls.append(
            current_document
        )
    )

    try:
        proxy = node_object.ForgeCADNodeProxy(
            node
        )

        proxy.onChanged(
            node,
            "Placement",
        )

    finally:
        node_object.rebuild_joint_status_after_topology_change = (
            original
        )

    assert calls == []
