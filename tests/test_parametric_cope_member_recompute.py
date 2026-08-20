"""Tests that member recompute refreshes parametric cope axes."""

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


class FakeProfile:
    outside_diameter = 44.45
    wall_thickness = 3.0


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

        self.Shape = None
        self.MemberLength = 0.0


def make_proxy():
    proxy = object.__new__(
        member_object.TubeMemberProxy
    )

    proxy._ready = True
    proxy._updating = False

    return proxy


def test_update_shape_refreshes_cope_axis_before_building_member_shape():
    obj = FakeMember()

    proxy = make_proxy()

    events = []

    original_sync_nodes = (
        member_object.sync_member_points_from_nodes
    )

    original_sync_cope = (
        member_object.sync_cope_axes_from_target_members
    )

    original_build = (
        member_object.build_member_shape
    )

    proxy._selected_profile = (
        lambda current_obj: FakeProfile()
    )

    proxy._update_profile_properties = (
        lambda current_obj, profile: None
    )

    member_object.sync_member_points_from_nodes = (
        lambda current_obj: events.append(
            "nodes"
        )
    )

    member_object.sync_cope_axes_from_target_members = (
        lambda current_obj: events.append(
            "cope"
        )
    )

    member_object.build_member_shape = (
        lambda current_obj,
        profile,
        shape_builder: (
            events.append(
                "shape"
            )
            or ("shape-result", 500.0)
        )
    )

    try:
        proxy.update_shape(
            obj
        )

    finally:
        member_object.sync_member_points_from_nodes = (
            original_sync_nodes
        )

        member_object.sync_cope_axes_from_target_members = (
            original_sync_cope
        )

        member_object.build_member_shape = (
            original_build
        )

    assert events == [
        "nodes",
        "cope",
        "shape",
    ]

    assert obj.Shape == "shape-result"

    assert obj.MemberLength == 500.0
