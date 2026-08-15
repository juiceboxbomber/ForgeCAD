"""Tests for bent structural members in joint detection."""

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Frame,
    Material,
    Member,
    Node,
    StraightRun,
    TubeProfile,
)
from forgecad.services.joint_service import (
    connected_members,
    detect_joints,
    member_touches_node,
)


def _material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def _profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def _bent_member(
    start,
    end,
):
    tube = BentTube(
        straight_runs=(
            StraightRun(
                500.0
            ),
            StraightRun(
                500.0
            ),
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

    return BentMember(
        start=start,
        end=end,
        tube=tube,
    )


def test_bent_member_touches_start_node():
    start = Node(
        0.0,
        0.0,
        0.0,
    )

    end = Node(
        600.0,
        600.0,
        0.0,
    )

    member = _bent_member(
        start,
        end,
    )

    assert member_touches_node(
        member,
        start,
    )


def test_bent_member_touches_end_node():
    start = Node(
        0.0,
        0.0,
        0.0,
    )

    end = Node(
        600.0,
        600.0,
        0.0,
    )

    member = _bent_member(
        start,
        end,
    )

    assert member_touches_node(
        member,
        end,
    )


def test_bent_member_does_not_use_start_end_chord_for_interior_node():
    start = Node(
        0.0,
        0.0,
        0.0,
    )

    end = Node(
        600.0,
        600.0,
        0.0,
    )

    member = _bent_member(
        start,
        end,
    )

    chord_midpoint = Node(
        300.0,
        300.0,
        0.0,
    )

    assert not member_touches_node(
        member,
        chord_midpoint,
    )


def test_connected_members_include_bent_member_at_shared_endpoint():
    joint_node = Node(
        600.0,
        600.0,
        0.0,
    )

    bent = _bent_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        joint_node,
    )

    straight = Member(
        start=joint_node,
        end=Node(
            1000.0,
            600.0,
            0.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    frame = Frame(
        members=[
            bent,
            straight,
        ]
    )

    assert connected_members(
        frame,
        joint_node,
    ) == [
        bent,
        straight,
    ]


def test_detect_joints_creates_joint_for_bent_and_straight_members():
    joint_node = Node(
        600.0,
        600.0,
        0.0,
    )

    bent = _bent_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        joint_node,
    )

    straight = Member(
        start=joint_node,
        end=Node(
            1000.0,
            600.0,
            0.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    frame = Frame(
        members=[
            bent,
            straight,
        ]
    )

    joints = detect_joints(
        frame
    )

    assert len(
        joints
    ) == 1

    assert joints[
        0
    ].node == joint_node

    assert joints[
        0
    ].members == [
        bent,
        straight,
    ]
    