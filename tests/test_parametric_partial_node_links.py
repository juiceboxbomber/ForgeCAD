"""Tests for parametric members with independently linked endpoints."""

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
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


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


import forgecad.adapters.freecad.member_object as member_object

from forgecad.adapters.freecad.member_object import (
    ensure_member_node_links,
    sync_member_points_from_nodes,
)


# Some existing tests import member_object before this test module.
# Make sure the module itself uses this test's Vector implementation.
member_object.FreeCAD.Vector = FakeVector


class FakeMemberObject:
    """Minimal FreeCAD-like straight member."""

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
    """Minimal linked ForgeCAD node."""

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
        float(point.x),
        float(point.y),
        float(point.z),
    )


def test_start_node_drives_only_start_endpoint():
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

    junction = FakeNode(
        0.0,
        0.0,
        0.0,
    )

    ensure_member_node_links(
        member,
        junction,
        None,
    )

    junction.Position = FakeVector(
        100.0,
        50.0,
        25.0,
    )

    changed = sync_member_points_from_nodes(
        member
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


def test_end_node_drives_only_end_endpoint():
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

    junction = FakeNode(
        0.0,
        0.0,
        0.0,
    )

    ensure_member_node_links(
        member,
        None,
        junction,
    )

    junction.Position = FakeVector(
        -75.0,
        25.0,
        10.0,
    )

    changed = sync_member_points_from_nodes(
        member
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


def test_member_without_node_links_keeps_stored_endpoints():
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

    changed = sync_member_points_from_nodes(
        member
    )

    assert changed is False

    assert point_tuple(
        member.StartPoint
    ) == before_start

    assert point_tuple(
        member.EndPoint
    ) == before_end
    