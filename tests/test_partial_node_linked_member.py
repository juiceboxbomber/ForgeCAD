"""Tests for members with one persistent node-linked endpoint."""

import importlib
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


def import_member_helpers():
    """
    Import member_object with temporary FreeCAD test doubles.

    The temporary modules are restored immediately afterward so this
    test cannot pollute other pytest modules during collection.
    """

    module_names = (
        "FreeCAD",
        "FreeCADGui",
        "Part",
        "PySide",
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

    fake_pyside.QtGui = (
        types.SimpleNamespace()
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

    try:
        module = importlib.import_module(
            "forgecad.adapters.freecad.member_object"
        )

        ensure_member_node_links = (
            module.ensure_member_node_links
        )

        sync_member_points_from_nodes = (
            module.sync_member_points_from_nodes
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

    return (
        ensure_member_node_links,
        sync_member_points_from_nodes,
    )


(
    ensure_member_node_links,
    sync_member_points_from_nodes,
) = import_member_helpers()


class FakeMemberObject:
    """Minimal straight-member object."""

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
    """Minimal ForgeCAD node."""

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


def point_tuple(
    point,
):
    return (
        float(
            point.x
        ),
        float(
            point.y
        ),
        float(
            point.z
        ),
    )


def test_start_node_can_move_without_end_node_link():
    member = FakeMemberObject(
        start=(
            0.0,
            0.0,
            0.0,
        ),
        end=(
            0.0,
            500.0,
            0.0,
        ),
    )

    junction_node = FakeNode(
        0.0,
        0.0,
        0.0,
    )

    ensure_member_node_links(
        member,
        junction_node,
        None,
    )

    junction_node.Position = (
        FakeVector(
            100.0,
            50.0,
            25.0,
        )
    )

    changed = (
        sync_member_points_from_nodes(
            member
        )
    )

    assert changed is True

    assert point_tuple(
        member.StartPoint
    ) == (
        100.0,
        50.0,
        25.0,
    )

    assert point_tuple(
        member.EndPoint
    ) == (
        0.0,
        500.0,
        0.0,
    )


def test_end_node_can_move_without_start_node_link():
    member = FakeMemberObject(
        start=(
            0.0,
            500.0,
            0.0,
        ),
        end=(
            0.0,
            0.0,
            0.0,
        ),
    )

    junction_node = FakeNode(
        0.0,
        0.0,
        0.0,
    )

    ensure_member_node_links(
        member,
        None,
        junction_node,
    )

    junction_node.Position = (
        FakeVector(
            -75.0,
            25.0,
            10.0,
        )
    )

    changed = (
        sync_member_points_from_nodes(
            member
        )
    )

    assert changed is True

    assert point_tuple(
        member.StartPoint
    ) == (
        0.0,
        500.0,
        0.0,
    )

    assert point_tuple(
        member.EndPoint
    ) == (
        -75.0,
        25.0,
        10.0,
    )


def test_member_without_any_node_links_is_unchanged():
    member = FakeMemberObject(
        start=(
            0.0,
            0.0,
            0.0,
        ),
        end=(
            0.0,
            500.0,
            0.0,
        ),
    )

    ensure_member_node_links(
        member,
        None,
        None,
    )

    before_start = point_tuple(
        member.StartPoint
    )

    before_end = point_tuple(
        member.EndPoint
    )

    changed = (
        sync_member_points_from_nodes(
            member
        )
    )

    assert changed is False

    assert point_tuple(
        member.StartPoint
    ) == before_start

    assert point_tuple(
        member.EndPoint
    ) == before_end
    