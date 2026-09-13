"""Tests that node edits touch dependencies without rebuilding derived geometry."""

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


class FakePlacement:
    def __init__(
        self,
        point,
    ):
        self.Base = FakeVector(
            *point
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


import forgecad.adapters.freecad.node_object as node_object


node_object.FreeCAD.Vector = FakeVector


class FakeDocument:
    pass


class FakeNode:
    def __init__(
        self,
        point,
    ):
        self.Position = FakeVector(
            *point
        )

        self.Placement = FakePlacement(
            point
        )

        self.X = float(
            point[0]
        )

        self.Y = float(
            point[1]
        )

        self.Z = float(
            point[2]
        )

        self.Document = FakeDocument()

        self.Proxy = None


def test_node_placement_change_rebuilds_connected_members():
    node = FakeNode(
        (
            0.0,
            0.0,
            0.0,
        )
    )

    proxy = node_object.ForgeCADNodeProxy(
        node
    )

    node.Placement.Base = FakeVector(
        100.0,
        50.0,
        25.0,
    )

    events = []

    original_layout_sync = (
        node_object.sync_layout_points_for_node
    )

    original_touch = (
        node_object.touch_connected_members
    )

    original_member_refresh = (
        node_object.refresh_connected_members
    )

    original_joint_rebuild = (
        node_object.rebuild_joint_status_after_topology_change
    )

    node_object.sync_layout_points_for_node = (
        lambda document,
        old_position,
        new_position,
        **kwargs: events.append(
            "layout"
        )
        or 0
)

    node_object.touch_connected_members = (
        lambda document,
        moved_node: events.append(
            "touch-members"
        )
        or ()
    )

    node_object.refresh_connected_members = (
        lambda document,
        moved_node: events.append(
            "rebuild-members"
        )
        or ()
    )

    node_object.rebuild_joint_status_after_topology_change = (
        lambda document: events.append(
            "joints"
        )
        or ()
    )

    try:
        proxy.onChanged(
            node,
            "Placement",
        )

    finally:
        node_object.sync_layout_points_for_node = (
            original_layout_sync
        )

        node_object.touch_connected_members = (
            original_touch
        )

        node_object.refresh_connected_members = (
            original_member_refresh
        )

        node_object.rebuild_joint_status_after_topology_change = (
            original_joint_rebuild
        )

    assert events == [
    "layout",
    "rebuild-members",
    ]

    assert (
        node.X,
        node.Y,
        node.Z,
    ) == (
        100.0,
        50.0,
        25.0,
    )
