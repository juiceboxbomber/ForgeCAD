"""Regression tests for node behavior during FreeCAD transaction replay."""

import importlib
import sys
import types


class FakeVector:
    def __init__(
        self,
        x=0.0,
        y=0.0,
        z=0.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class FakePlacement:
    def __init__(
        self,
        x=0.0,
        y=0.0,
        z=0.0,
    ):
        self.Base = FakeVector(
            x,
            y,
            z,
        )


class FakeDocument:
    def __init__(
        self,
        restoring=False,
    ):
        self.restoring = bool(
            restoring
        )

    def isPerformingTransaction(
        self,
    ):
        return self.restoring


class FakeNode:
    def __init__(
        self,
        document,
        point=(0.0, 0.0, 0.0),
    ):
        self.Document = document
        self.Position = FakeVector(
            *point
        )
        self.Placement = FakePlacement(
            *point
        )
        self.X = float(point[0])
        self.Y = float(point[1])
        self.Z = float(point[2])
        self.Proxy = None


def import_node_module():
    module_names = (
        "FreeCAD",
        "Part",
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
    fake_freecad.Vector = FakeVector

    fake_part = types.ModuleType(
        "Part"
    )

    sys.modules[
        "FreeCAD"
    ] = fake_freecad
    sys.modules[
        "Part"
    ] = fake_part

    try:
        module = importlib.import_module(
            "forgecad.adapters.freecad.node_object"
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


node_object = import_node_module()


def test_transaction_replay_detection():
    assert (
        node_object.document_is_restoring_transaction(
            FakeDocument(
                restoring=False
            )
        )
        is False
    )

    assert (
        node_object.document_is_restoring_transaction(
            FakeDocument(
                restoring=True
            )
        )
        is True
    )


def test_onchanged_does_not_propagate_topology_during_transaction_replay():
    document = FakeDocument(
        restoring=True
    )

    node = FakeNode(
        document,
        point=(
            0.0,
            0.0,
            0.0,
        ),
    )

    proxy = (
        node_object.ForgeCADNodeProxy(
            node
        )
    )

    node.Placement.Base = FakeVector(
        100.0,
        200.0,
        300.0,
    )

    calls = []

    original_layout = (
        node_object.sync_layout_points_for_node
    )
    original_members = (
        node_object.refresh_connected_members
    )
    original_joints = (
        node_object.rebuild_joint_status_after_topology_change
    )

    node_object.sync_layout_points_for_node = (
        lambda *args, **kwargs: calls.append(
            "layout"
        )
    )
    node_object.refresh_connected_members = (
        lambda *args, **kwargs: calls.append(
            "members"
        )
    )
    node_object.rebuild_joint_status_after_topology_change = (
        lambda *args, **kwargs: calls.append(
            "joints"
        )
    )

    try:
        proxy.onChanged(
            node,
            "Placement",
        )
    finally:
        node_object.sync_layout_points_for_node = (
            original_layout
        )
        node_object.refresh_connected_members = (
            original_members
        )
        node_object.rebuild_joint_status_after_topology_change = (
            original_joints
        )

    assert calls == []

    assert proxy._last_position == (
        100.0,
        200.0,
        300.0,
    )

    # FreeCAD owns restoration of these mirrored properties during replay.
    assert (
        node.Position.x,
        node.Position.y,
        node.Position.z,
    ) == (
        0.0,
        0.0,
        0.0,
    )


def test_execute_is_read_only_during_transaction_replay():
    document = FakeDocument(
        restoring=True
    )

    node = FakeNode(
        document,
        point=(
            10.0,
            20.0,
            30.0,
        ),
    )

    proxy = (
        node_object.ForgeCADNodeProxy(
            node
        )
    )

    node.Placement.Base = FakeVector(
        50.0,
        60.0,
        70.0,
    )

    before_position = node.Position
    before_xyz = (
        node.X,
        node.Y,
        node.Z,
    )

    proxy.execute(
        node
    )

    assert node.Position is before_position

    assert (
        node.X,
        node.Y,
        node.Z,
    ) == before_xyz

    assert proxy._last_position == (
        50.0,
        60.0,
        70.0,
    )
