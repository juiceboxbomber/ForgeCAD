"""Tests for member geometry derived from node links during recompute."""

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


member_object.FreeCAD.Vector = FakeVector


class FakeNode:
    def __init__(
        self,
        point,
    ):
        self.Position = FakeVector(
            *point
        )


class FakeMember:
    def __init__(
        self,
    ):
        self.StartPoint = FakeVector(
            0.0,
            0.0,
            0.0,
        )

        self.EndPoint = FakeVector(
            0.0,
            500.0,
            0.0,
        )

        self.StartNode = None
        self.EndNode = None


def point_tuple(
    point,
):
    return (
        float(point.x),
        float(point.y),
        float(point.z),
    )


def make_proxy():
    proxy = object.__new__(
        member_object.TubeMemberProxy
    )

    proxy._ready = True
    proxy._updating = False

    return proxy


def test_execute_syncs_linked_endpoint_before_rebuilding_shape():
    member = FakeMember()

    junction = FakeNode(
        (
            100.0,
            50.0,
            25.0,
        )
    )

    member.StartNode = junction

    proxy = make_proxy()

    events = []

    proxy.update_shape = (
        lambda obj: events.append(
            (
                "shape",
                point_tuple(
                    obj.StartPoint
                ),
                point_tuple(
                    obj.EndPoint
                ),
            )
        )
    )

    proxy._update_label = (
        lambda obj: events.append(
            (
                "label",
                point_tuple(
                    obj.StartPoint
                ),
            )
        )
    )

    proxy.execute(
        member
    )

    assert events == [
        (
            "shape",
            (
                100.0,
                50.0,
                25.0,
            ),
            (
                0.0,
                500.0,
                0.0,
            ),
        ),
        (
            "label",
            (
                100.0,
                50.0,
                25.0,
            ),
        ),
    ]
    