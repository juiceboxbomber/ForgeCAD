"""Tests for persistent node links on ForgeCAD straight members."""

import sys
import types


class FakeVector:
    """Minimal FreeCAD.Vector replacement."""

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


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.Vector = (
    FakeVector
)

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_part = types.ModuleType(
    "Part"
)

fake_pyside = types.ModuleType(
    "PySide"
)


class FakeDialog:
    """Minimal Qt dialog base used by later command imports."""

    pass


fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=FakeDialog,
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


from forgecad.adapters.freecad.member_object import (
    ensure_member_node_links,
    sync_member_points_from_nodes,
)


class FakeMemberObject:
    """Minimal FreeCAD-like member object."""

    def __init__(
        self,
    ):
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


class FakeNode:
    def __init__(
        self,
        x=0.0,
        y=0.0,
        z=0.0,
    ):
        self.Position = FakeVector(
            x,
            y,
            z,
        )


def test_member_node_links_are_created():
    member = FakeMemberObject()

    start_node = FakeNode()
    end_node = FakeNode()

    ensure_member_node_links(
        member,
        start_node,
        end_node,
    )

    assert (
        "App::PropertyLink",
        "StartNode",
        "ForgeCAD Topology",
    ) in member.added_properties

    assert (
        "App::PropertyLink",
        "EndNode",
        "ForgeCAD Topology",
    ) in member.added_properties


def test_member_node_links_reference_exact_nodes():
    member = FakeMemberObject()

    start_node = FakeNode()
    end_node = FakeNode()

    ensure_member_node_links(
        member,
        start_node,
        end_node,
    )

    assert (
        member.StartNode
        is start_node
    )

    assert (
        member.EndNode
        is end_node
    )


def test_existing_link_properties_are_reused():
    member = FakeMemberObject()

    member.StartNode = None
    member.EndNode = None

    start_node = FakeNode()
    end_node = FakeNode()

    ensure_member_node_links(
        member,
        start_node,
        end_node,
    )

    assert member.added_properties == []

    assert (
        member.StartNode
        is start_node
    )

    assert (
        member.EndNode
        is end_node
    )


def test_member_creation_helper_keeps_exact_node_identity():
    member = FakeMemberObject()

    start_node = FakeNode()
    end_node = FakeNode()

    ensure_member_node_links(
        member,
        start_node,
        end_node,
    )

    assert (
        member.StartNode
        is start_node
    )

    assert (
        member.EndNode
        is end_node
    )


def test_sync_member_points_from_nodes_updates_coordinates():
    member = FakeMemberObject()

    member.StartPoint = FakeVector(
        0.0,
        0.0,
        0.0,
    )

    member.EndPoint = FakeVector(
        100.0,
        0.0,
        0.0,
    )

    start_node = FakeNode(
        10.0,
        20.0,
        30.0,
    )

    end_node = FakeNode(
        400.0,
        500.0,
        600.0,
    )

    ensure_member_node_links(
        member,
        start_node,
        end_node,
    )

    result = (
        sync_member_points_from_nodes(
            member
        )
    )

    assert result is True

    assert (
        member.StartPoint.x,
        member.StartPoint.y,
        member.StartPoint.z,
    ) == (
        10.0,
        20.0,
        30.0,
    )

    assert (
        member.EndPoint.x,
        member.EndPoint.y,
        member.EndPoint.z,
    ) == (
        400.0,
        500.0,
        600.0,
    )


def test_sync_member_points_without_links_does_nothing():
    member = FakeMemberObject()

    member.StartPoint = FakeVector(
        0.0,
        0.0,
        0.0,
    )

    member.EndPoint = FakeVector(
        100.0,
        0.0,
        0.0,
    )

    result = (
        sync_member_points_from_nodes(
            member
        )
    )

    assert result is False

    assert member.StartPoint.x == 0.0
    assert member.EndPoint.x == 100.0
