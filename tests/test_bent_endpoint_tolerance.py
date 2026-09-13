"""Regression tests for solved bent endpoints at persistent CAD joints."""

import pytest

from forgecad.fabrication import (
    Bend, BentMember, BentTube, Frame, Joint, Material, Member,
    Node, StraightRun, TubeProfile,
)
from forgecad.geometry import Vector3D
from forgecad.services.joint_extension import (
    MEMBER_END_END,
    member_end_at_joint as extension_member_end_at_joint,
)
from forgecad.services.joint_geometry import (
    member_direction_from_node,
    member_point_parameter,
)
from forgecad.services.joint_miter import (
    MITER_END_END,
    member_direction_from_joint,
    member_end_at_joint as miter_member_end_at_joint,
)
from forgecad.services.joint_service import detect_joints, member_touches_node


PROFILE = TubeProfile(outside_diameter=44.45, wall_thickness=3.048)
MATERIAL = Material(name="DOM", density=7850.0, yield_strength=350.0)


def bent_member(end_x=600.0000004):
    tube = BentTube(
        straight_runs=(StraightRun(500.0), StraightRun(500.0)),
        bends=(Bend(angle_degrees=90.0, centerline_radius=100.0),),
        profile=PROFILE,
        material=MATERIAL,
    )
    return BentMember(
        start=Node(0.0, 0.0, 0.0),
        end=Node(end_x, 600.0, 0.0),
        tube=tube,
        initial_direction=Vector3D(1.0, 0.0, 0.0),
        initial_bend_normal=Vector3D(0.0, 0.0, 1.0),
    )


def test_bent_endpoint_touches_nearby_persistent_node():
    assert member_touches_node(bent_member(), Node(600.0, 600.0, 0.0))


def test_bent_endpoint_parameter_uses_tolerance():
    assert member_point_parameter(
        bent_member(), Node(600.0, 600.0, 0.0)
    ) == 1.0


def test_bent_end_direction_uses_true_local_tangent_with_epsilon():
    direction = member_direction_from_node(
        bent_member(), Node(600.0, 600.0, 0.0)
    )
    assert direction == pytest.approx((0.0, -1.0, 0.0), abs=1e-7)


def test_miter_and_extension_end_resolution_accept_epsilon():
    bent = bent_member()
    joint = Joint(
        node=Node(600.0, 600.0, 0.0),
        members=[bent],
    )
    assert miter_member_end_at_joint(bent, joint) == MITER_END_END
    assert extension_member_end_at_joint(bent, joint) == MEMBER_END_END


def test_miter_direction_uses_bent_tangent_not_chord():
    bent = bent_member()
    joint = Joint(node=Node(600.0, 600.0, 0.0), members=[bent])
    direction = member_direction_from_joint(bent, joint)
    assert direction.x == pytest.approx(0.0, abs=1e-7)
    assert direction.y == pytest.approx(-1.0, abs=1e-7)


def test_detect_joints_deduplicates_near_equal_endpoints():
    bent = bent_member()
    straight = Member(
        start=Node(600.0, 600.0, 0.0),
        end=Node(1000.0, 600.0, 0.0),
        profile=PROFILE,
        material=MATERIAL,
    )
    joints = detect_joints(Frame(members=[bent, straight]))
    assert len(joints) == 1
    assert joints[0].member_count == 2
