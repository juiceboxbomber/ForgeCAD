"""Tests for persistent bent-tube endpoint topology."""

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

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad.bent_tube_object import (
    ensure_bent_tube_node_links,
    sync_bent_tube_end_node,
    sync_bent_tube_start_from_node,
)


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


class FakeBentObject:
    def __init__(
        self,
    ):
        self.StartPoint = FakeVector(
            0.0,
            0.0,
            0.0,
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


class FakePoint:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class FakeCenterline:
    def __init__(
        self,
        end_point,
    ):
        self.end_point = end_point


def test_bent_tube_links_store_exact_nodes():
    obj = FakeBentObject()

    start = FakeNode(
        0.0,
        0.0,
        0.0,
    )
    end = FakeNode(
        100.0,
        100.0,
        0.0,
    )

    ensure_bent_tube_node_links(
        obj,
        start,
        end,
    )

    assert obj.StartNode is start
    assert obj.EndNode is end

    assert (
        "App::PropertyLink",
        "StartNode",
        "ForgeCAD Topology",
    ) in obj.added_properties

    assert (
        "App::PropertyLink",
        "EndNode",
        "ForgeCAD Topology",
    ) in obj.added_properties


def test_start_node_drives_bent_tube_start_point():
    obj = FakeBentObject()

    obj.StartNode = FakeNode(
        10.0,
        20.0,
        30.0,
    )

    result = sync_bent_tube_start_from_node(
        obj
    )

    assert result is True

    assert (
        obj.StartPoint.x,
        obj.StartPoint.y,
        obj.StartPoint.z,
    ) == (
        10.0,
        20.0,
        30.0,
    )


def test_solved_endpoint_drives_end_node_placement():
    obj = FakeBentObject()

    obj.EndNode = FakeNode(
        0.0,
        0.0,
        0.0,
    )

    centerline = FakeCenterline(
        FakePoint(
            600.0,
            600.0,
            0.0,
        )
    )

    result = sync_bent_tube_end_node(
        obj,
        centerline,
    )

    assert result is True

    assert (
        obj.EndNode.Placement.Base.x,
        obj.EndNode.Placement.Base.y,
        obj.EndNode.Placement.Base.z,
    ) == (
        600.0,
        600.0,
        0.0,
    )
