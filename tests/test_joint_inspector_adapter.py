"""Tests for the FreeCAD Joint Inspector adapter."""

import sys
import types


# ---------------------------------------------------------
# Minimal FreeCAD stubs
# ---------------------------------------------------------

freecad = types.ModuleType(
    "FreeCAD"
)

freecadgui = types.ModuleType(
    "FreeCADGui"
)

part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = freecad

sys.modules[
    "FreeCADGui"
] = freecadgui

sys.modules[
    "Part"
] = part


from forgecad.adapters.freecad.joint_inspector_adapter import (
    frame_member_objects,
    is_forgecad_member,
    is_forgecad_node,
    joint_from_node_object,
    member_from_freecad_object,
    member_touches_node,
    node_from_freecad_object,
)


class FakeVector:
    """Minimal FreeCAD-like vector."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


class FakeNodeObject:
    """Minimal generated ForgeCAD node."""

    def __init__(
        self,
        node_id,
        x,
        y,
        z,
    ):
        self.NodeID = node_id
        self.Position = FakeVector(
            x,
            y,
            z,
        )


class FakeMemberObject:
    """Minimal generated ForgeCAD member."""

    def __init__(
        self,
        member_id,
        start,
        end,
        tube_profile=(
            "1.750 x .120 DOM"
        ),
    ):
        self.MemberID = member_id
        self.TubeProfile = (
            tube_profile
        )
        self.StartPoint = start
        self.EndPoint = end


class FakeUnrelatedObject:
    """Object that is neither a ForgeCAD node nor member."""

    pass


class FakeFrameGroup:
    """Minimal FreeCAD Frame group."""

    def __init__(
        self,
        objects,
    ):
        self.Group = list(
            objects
        )


class FakeDocument:
    """Minimal FreeCAD document."""

    def __init__(
        self,
        frame_objects=None,
    ):
        self.frame_group = (
            FakeFrameGroup(
                frame_objects or []
            )
        )

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADFrame":
            return self.frame_group

        return None


def test_identifies_forgecad_node():
    node = FakeNodeObject(
        "N001",
        0,
        0,
        0,
    )

    assert is_forgecad_node(
        node
    )

    assert not is_forgecad_node(
        FakeUnrelatedObject()
    )


def test_identifies_forgecad_member():
    member = FakeMemberObject(
        "M001",
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            500,
            0,
            0,
        ),
    )

    assert is_forgecad_member(
        member
    )

    assert not is_forgecad_member(
        FakeUnrelatedObject()
    )


def test_builds_domain_node():
    node_object = FakeNodeObject(
        "N001",
        10,
        20,
        30,
    )

    node = node_from_freecad_object(
        node_object
    )

    assert node.x == 10.0
    assert node.y == 20.0
    assert node.z == 30.0


def test_builds_domain_member():
    member_object = FakeMemberObject(
        "M001",
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            500,
            0,
            0,
        ),
    )

    member = (
        member_from_freecad_object(
            member_object
        )
    )

    assert member.start.x == 0.0
    assert member.end.x == 500.0

    assert (
        member.profile.outside_diameter
        > 0.0
    )

    assert (
        member.material
        is not None
    )


def test_member_touch_detection():
    member_object = FakeMemberObject(
        "M001",
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            500,
            0,
            0,
        ),
    )

    member = (
        member_from_freecad_object(
            member_object
        )
    )

    start_node = (
        node_from_freecad_object(
            FakeNodeObject(
                "N001",
                0,
                0,
                0,
            )
        )
    )

    unrelated_node = (
        node_from_freecad_object(
            FakeNodeObject(
                "N002",
                0,
                500,
                0,
            )
        )
    )

    assert member_touches_node(
        member,
        start_node,
    )

    assert not member_touches_node(
        member,
        unrelated_node,
    )


def test_returns_frame_member_objects():
    member_1 = FakeMemberObject(
        "M001",
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            -500,
            0,
            0,
        ),
    )

    member_2 = FakeMemberObject(
        "M002",
        FakeVector(
            0,
            0,
            0,
        ),
        FakeVector(
            500,
            0,
            0,
        ),
    )

    unrelated = (
        FakeUnrelatedObject()
    )

    document = FakeDocument(
        [
            member_1,
            unrelated,
            member_2,
        ]
    )

    result = (
        frame_member_objects(
            document
        )
    )

    assert result == [
        member_1,
        member_2,
    ]


def test_builds_joint_from_selected_node():
    center = FakeVector(
        0,
        0,
        0,
    )

    left = FakeMemberObject(
        "M001",
        center,
        FakeVector(
            -500,
            0,
            0,
        ),
    )

    right = FakeMemberObject(
        "M002",
        center,
        FakeVector(
            500,
            0,
            0,
        ),
    )

    branch = FakeMemberObject(
        "M003",
        center,
        FakeVector(
            0,
            500,
            0,
        ),
    )

    unrelated = FakeMemberObject(
        "M004",
        FakeVector(
            1000,
            0,
            0,
        ),
        FakeVector(
            1500,
            0,
            0,
        ),
    )

    document = FakeDocument(
        [
            left,
            right,
            branch,
            unrelated,
        ]
    )

    node_object = FakeNodeObject(
        "N001",
        0,
        0,
        0,
    )

    joint = joint_from_node_object(
        document,
        node_object,
    )

    assert joint.node.x == 0.0
    assert joint.node.y == 0.0
    assert joint.node.z == 0.0

    assert (
        joint.member_count
        == 3
    )
    