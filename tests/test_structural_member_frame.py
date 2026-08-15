"""Tests for straight and bent structural members in frames."""

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Frame,
    Joint,
    Material,
    Member,
    Node,
    StraightRun,
    TubeProfile,
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


def _bent_member():
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
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            600.0,
            600.0,
            0.0,
        ),
        tube=tube,
    )


def test_frame_accepts_straight_and_bent_members():
    frame = Frame()

    straight = Member(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            1000.0,
            0.0,
            0.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    bent = _bent_member()

    frame.add_member(
        straight
    )

    frame.add_member(
        bent
    )

    assert frame.member_count == 2
    assert frame.members == [
        straight,
        bent,
    ]


def test_joint_accepts_straight_and_bent_members():
    node = Node(
        0.0,
        0.0,
        0.0,
    )

    straight = Member(
        start=node,
        end=Node(
            1000.0,
            0.0,
            0.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    bent = _bent_member()

    joint = Joint(
        node=node,
    )

    joint.add_member(
        straight
    )

    joint.add_member(
        bent
    )

    assert joint.member_count == 2
    assert joint.members == [
        straight,
        bent,
    ]
    