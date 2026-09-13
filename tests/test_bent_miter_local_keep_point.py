"""Bent-member miter keep points must stay local to the endpoint."""

import pytest

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Joint,
    Material,
    Node,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import (
    Vector3D,
)
from forgecad.services.joint_miter import (
    member_keep_point,
)


PROFILE = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)

MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


def _member():
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
        tube=BentTube(
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
            profile=PROFILE,
            material=MATERIAL,
        ),
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


def test_bent_start_keep_point_follows_local_inward_tangent():
    member = _member()

    joint = Joint(
        node=member.start,
        members=[
            member
        ],
    )

    keep = member_keep_point(
        member,
        joint,
    )

    assert keep == pytest.approx(
        (
            44.45,
            0.0,
            0.0,
        ),
        abs=1e-8,
    )


def test_bent_end_keep_point_follows_reversed_final_tangent():
    member = _member()

    joint = Joint(
        node=member.end,
        members=[
            member
        ],
    )

    keep = member_keep_point(
        member,
        joint,
    )

    assert keep == pytest.approx(
        (
            600.0,
            600.0 - 44.45,
            0.0,
        ),
        abs=1e-8,
    )


def test_bent_keep_point_is_not_the_distant_opposite_endpoint():
    member = _member()

    joint = Joint(
        node=member.end,
        members=[
            member
        ],
    )

    assert (
        member_keep_point(
            member,
            joint,
        )
        != (
            member.start.x,
            member.start.y,
            member.start.z,
        )
    )
