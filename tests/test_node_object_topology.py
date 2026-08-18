"""Tests for parametric ForgeCAD node topology behavior."""

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


class FakePart:
    @staticmethod
    def makeSphere(
        radius,
        point,
    ):
        return (
            "sphere",
            float(radius),
            point,
        )

    @staticmethod
    def makeLine(
        start,
        end,
    ):
        return (
            "line",
            start,
            end,
        )


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.Vector = FakeVector

fake_part = types.ModuleType(
    "Part"
)
fake_part.makeSphere = (
    FakePart.makeSphere
)
fake_part.makeLine = (
    FakePart.makeLine
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "Part"
] = fake_part


import forgecad.adapters.freecad.node_object as node_object

from forgecad.adapters.freecad.node_object import (
    ForgeCADNodeProxy,
    connected_member_objects,
    point_key,
    sync_layout_points_for_node,
)


class FakeLayoutObject:
    def __init__(
        self,
        start,
        end,
    ):
        self.StartPoint = FakeVector(
            *start
        )
        self.EndPoint = FakeVector(
            *end
        )
        self.Shape = None
        self.Proxy = None
        self.touched = False

    def touch(self):
        self.touched = True


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
        layout_objects=(),
        objects=(),
    ):
        self.layout_group = FakeGroup(
            layout_objects
        )
        self.Objects = list(
            objects
        )

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADLayout":
            return self.layout_group

        return None


class FakeMemberProxy:
    def __init__(self):
        self.calls = 0

    def update_shape(
        self,
        obj,
    ):
        self.calls += 1


class FakeMember:
    def __init__(
        self,
        start_node=None,
        end_node=None,
    ):
        self.StartNode = start_node
        self.EndNode = end_node
        self.Proxy = FakeMemberProxy()
        self.touched = False

    def touch(self):
        self.touched = True


class FakePlacement:
    def __init__(
        self,
        position,
    ):
        self.Base = FakeVector(
            *position
        )


class FakeNode:
    def __init__(
        self,
        position,
    ):
        self.Position = FakeVector(
            *position
        )
        self.Placement = FakePlacement(
            position
        )
        self.X = float(position[0])
        self.Y = float(position[1])
        self.Z = float(position[2])
        self.Shape = None
        self.Proxy = None
        self.Document = None


def test_point_key_is_stable():
    assert point_key(
        FakeVector(
            1.0000004,
            2.0,
            3.0,
        )
    ) == (
        1.0,
        2.0,
        3.0,
    )


def test_connected_members_use_exact_node_links():
    node = FakeNode(
        (0, 0, 0)
    )
    other = FakeNode(
        (100, 0, 0)
    )

    first = FakeMember(
        start_node=node,
        end_node=other,
    )
    second = FakeMember(
        start_node=other,
        end_node=node,
    )
    unrelated = FakeMember(
        start_node=other,
        end_node=other,
    )

    document = FakeDocument(
        objects=(
            first,
            second,
            unrelated,
        )
    )

    assert connected_member_objects(
        document,
        node,
    ) == [
        first,
        second,
    ]


def test_layout_endpoints_follow_moved_node():
    first = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )
    second = FakeLayoutObject(
        (0, 0, 0),
        (0, 500, 0),
    )

    document = FakeDocument(
        layout_objects=(
            first,
            second,
        )
    )

    changed = sync_layout_points_for_node(
        document,
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            10,
            20,
            30,
        ),
    )

    assert changed == 2

    assert point_key(
        first.StartPoint
    ) == (
        10.0,
        20.0,
        30.0,
    )

    assert point_key(
        second.StartPoint
    ) == (
        10.0,
        20.0,
        30.0,
    )

    assert first.touched
    assert second.touched


def test_layout_interior_is_not_split_when_node_moves():
    layout = FakeLayoutObject(
        (-100, 0, 0),
        (100, 0, 0),
    )

    document = FakeDocument(
        layout_objects=(
            layout,
        )
    )

    changed = sync_layout_points_for_node(
        document,
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            0,
            50,
            0,
        ),
    )

    assert changed == 0

    assert point_key(
        layout.StartPoint
    ) == (
        -100.0,
        0.0,
        0.0,
    )

    assert point_key(
        layout.EndPoint
    ) == (
        100.0,
        0.0,
        0.0,
    )


def test_node_proxy_propagates_placement_change():
    node = FakeNode(
        (0, 0, 0)
    )
    other = FakeNode(
        (1000, 0, 0)
    )

    layout = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    member = FakeMember(
        start_node=node,
        end_node=other,
    )

    document = FakeDocument(
        layout_objects=(
            layout,
        ),
        objects=(
            member,
        ),
    )

    node.Document = document

    proxy = ForgeCADNodeProxy(
        node
    )

    node.Placement.Base = FakeVector(
        10,
        20,
        30,
    )

    original_rebuild = (
        node_object.rebuild_joint_status_after_topology_change
    )

    node_object.rebuild_joint_status_after_topology_change = (
        lambda document: ()
    )

    try:
        proxy.onChanged(
            node,
            "Placement",
        )
    finally:
        node_object.rebuild_joint_status_after_topology_change = (
            original_rebuild
        )

    assert (
        node.X,
        node.Y,
        node.Z,
    ) == (
        10.0,
        20.0,
        30.0,
    )

    assert point_key(
        layout.StartPoint
    ) == (
        10.0,
        20.0,
        30.0,
    )

    assert member.Proxy.calls == 1
    assert member.touched
