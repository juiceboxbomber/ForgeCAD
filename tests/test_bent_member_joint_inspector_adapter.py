"""Tests for bent-member reconstruction in the joint inspector adapter."""

from types import SimpleNamespace

import pytest
import sys
import types

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)

fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad.joint_inspector_adapter import (
    bent_member_from_freecad_object,
    frame_member_objects,
    is_forgecad_bent_member,
    joint_from_node_object,
    structural_member_from_freecad_object,
)


def _profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def _material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def _tube():
    return BentTube(
        straight_runs=(
            StraightRun(500.0),
            StraightRun(500.0),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


class FakeBentProxy:
    def __init__(
        self,
        tube,
    ):
        self.tube = tube

    def _tube_from_properties(
        self,
        obj,
    ):
        return self.tube


def _bent_object():
    return SimpleNamespace(
        StartPoint=SimpleNamespace(
            x=0.0,
            y=0.0,
            z=0.0,
        ),
        InitialDirection=SimpleNamespace(
            x=1.0,
            y=0.0,
            z=0.0,
        ),
        InitialBendNormal=SimpleNamespace(
            x=0.0,
            y=0.0,
            z=1.0,
        ),
        TubeProfile="1.750 x .120 DOM",
        BendCount=1,
        Proxy=FakeBentProxy(
            _tube()
        ),
    )


def _straight_object():
    return SimpleNamespace(
        MemberID="M1",
        TubeProfile="1.750 x .120 DOM",
        StartPoint=SimpleNamespace(
            x=600.0,
            y=600.0,
            z=0.0,
        ),
        EndPoint=SimpleNamespace(
            x=1000.0,
            y=600.0,
            z=0.0,
        ),
    )


def _node_object():
    return SimpleNamespace(
        NodeID="N1",
        Position=SimpleNamespace(
            x=600.0,
            y=600.0,
            z=0.0,
        ),
    )


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
        straight_objects=(),
        bent_objects=(),
    ):
        self.objects = {
            "ForgeCADFrame": FakeGroup(
                straight_objects
            ),
            "ForgeCADBentTubes": FakeGroup(
                bent_objects
            ),
        }

    def getObject(
        self,
        name,
    ):
        return self.objects.get(
            name
        )


def test_bent_object_is_recognized_as_structural_member():
    assert is_forgecad_bent_member(
        _bent_object()
    )


def test_bent_member_reconstruction_uses_solved_endpoint():
    member = bent_member_from_freecad_object(
        _bent_object()
    )

    assert isinstance(
        member,
        BentMember,
    )

    assert (
        member.start.x,
        member.start.y,
        member.start.z,
    ) == pytest.approx(
        (
            0.0,
            0.0,
            0.0,
        )
    )

    assert (
        member.end.x,
        member.end.y,
        member.end.z,
    ) == pytest.approx(
        (
            600.0,
            600.0,
            0.0,
        ),
        abs=1e-9,
    )


def test_structural_member_dispatch_returns_bent_member():
    member = structural_member_from_freecad_object(
        _bent_object()
    )

    assert isinstance(
        member,
        BentMember,
    )


def test_frame_member_objects_include_straight_and_bent_groups():
    straight = _straight_object()
    bent = _bent_object()

    document = FakeDocument(
        straight_objects=(
            straight,
        ),
        bent_objects=(
            bent,
        ),
    )

    assert frame_member_objects(
        document
    ) == [
        straight,
        bent,
    ]


def test_joint_from_node_includes_bent_and_straight_member():
    document = FakeDocument(
        straight_objects=(
            _straight_object(),
        ),
        bent_objects=(
            _bent_object(),
        ),
    )

    joint = joint_from_node_object(
        document,
        _node_object(),
    )

    assert joint.member_count == 2

    assert isinstance(
        joint.members[
            0
        ],
        object,
    )

    assert any(
        isinstance(
            member,
            BentMember,
        )
        for member in joint.members
    )
