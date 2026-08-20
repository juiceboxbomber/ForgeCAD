"""Tests for joint geometry involving bent structural members."""

import pytest

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Joint,
    Material,
    Member,
    Node,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import Vector3D
from forgecad.services.joint_geometry import (
    JOINT_CORNER,
    JOINT_STRAIGHT,
    angle_between_members,
    classify_joint,
    member_contains_node_interior,
    member_direction_from_node,
    member_point_parameter,
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
    """
    Build a planar 90-degree bent member.

    Geometry:
        start = (0, 0, 0)
        500 mm along +X
        90-degree bend, 100 mm CLR
        500 mm along +Y
        end = (600, 600, 0)
    """

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
        initial_direction=Vector3D(
            1.0,
            0.0,
            0.0,
        ),
        initial_bend_normal=Vector3D(
            0.0,
            0.0,
            1.0,
        ),
    )


def test_bent_member_start_direction_uses_initial_tangent():
    member = _bent_member()

    direction = member_direction_from_node(
        member,
        member.start,
    )

    assert direction == pytest.approx(
        (
            1.0,
            0.0,
            0.0,
        )
    )


def test_bent_member_end_direction_uses_reversed_final_tangent():
    member = _bent_member()

    direction = member_direction_from_node(
        member,
        member.end,
    )

    assert direction == pytest.approx(
        (
            0.0,
            -1.0,
            0.0,
        ),
        abs=1e-9,
    )


def test_bent_member_only_exposes_endpoint_parameters():
    member = _bent_member()

    assert member_point_parameter(
        member,
        member.start,
    ) == pytest.approx(
        0.0
    )

    assert member_point_parameter(
        member,
        member.end,
    ) == pytest.approx(
        1.0
    )

    assert member_point_parameter(
        member,
        Node(
            300.0,
            300.0,
            0.0,
        ),
    ) is None


def test_bent_member_has_no_interior_joint_support_yet():
    member = _bent_member()

    assert not member_contains_node_interior(
        member,
        Node(
            500.0,
            100.0,
            0.0,
        ),
    )


def test_bent_member_and_perpendicular_straight_member_form_corner():
    bent = _bent_member()

    straight = Member(
        start=bent.end,
        end=Node(
            1000.0,
            600.0,
            0.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    angle = angle_between_members(
        bent,
        straight,
        bent.end,
    )

    assert angle == pytest.approx(
        90.0
    )

    joint = Joint(
        node=bent.end,
        members=[
            bent,
            straight,
        ],
    )

    assert classify_joint(
        joint
    ) == JOINT_CORNER


def test_bent_member_and_tangent_straight_member_form_straight_joint():
    bent = _bent_member()

    straight = Member(
        start=bent.end,
        end=Node(
            600.0,
            1000.0,
            0.0,
        ),
        profile=_profile(),
        material=_material(),
    )

    angle = angle_between_members(
        bent,
        straight,
        bent.end,
    )

    assert angle == pytest.approx(
        180.0
    )

    joint = Joint(
        node=bent.end,
        members=[
            bent,
            straight,
        ],
    )

    assert classify_joint(
        joint
    ) == JOINT_STRAIGHT
