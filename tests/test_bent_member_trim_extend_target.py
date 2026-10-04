"""Straight-source -> bent-target Trim / Extend geometry."""

import pytest

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Material,
    Member,
    Node,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import Vector3D
from forgecad.services.member_trim_extend import (
    straight_to_bent_endpoint_intersection_3d,
)


def profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def material():
    return Material(
        name="DOM Steel",
        density=7850.0,
        yield_strength=350.0,
    )


def target():
    return BentMember(
        start=Node(0.0, 0.0, 0.0),
        end=Node(150.0, 170.0, 0.0),
        tube=BentTube(
            straight_runs=(
                StraightRun(100.0),
                StraightRun(120.0),
            ),
            bends=(
                Bend(
                    angle_degrees=90.0,
                    centerline_radius=50.0,
                ),
            ),
            profile=profile(),
            material=material(),
        ),
        initial_direction=Vector3D(1.0, 0.0, 0.0),
        initial_bend_normal=Vector3D(0.0, 0.0, 1.0),
    )


def test_start_endpoint_tangent_is_used():
    source = Member(
        start=Node(0.0, 40.0, 0.0),
        end=Node(0.0, 10.0, 0.0),
        profile=profile(),
        material=material(),
    )

    intersection, source_parameter, _ = (
        straight_to_bent_endpoint_intersection_3d(
            source,
            target(),
            "start",
        )
    )

    assert intersection == Node(0.0, 0.0, 0.0)
    assert source_parameter > 1.0


def test_end_endpoint_tangent_is_used():
    source = Member(
        start=Node(190.0, 170.0, 0.0),
        end=Node(160.0, 170.0, 0.0),
        profile=profile(),
        material=material(),
    )

    intersection, source_parameter, _ = (
        straight_to_bent_endpoint_intersection_3d(
            source,
            target(),
            "end",
        )
    )

    assert intersection == Node(150.0, 170.0, 0.0)
    assert source_parameter > 1.0


def test_explicit_bent_target_endpoint_is_required():
    source = Member(
        start=Node(0.0, 40.0, 0.0),
        end=Node(0.0, 10.0, 0.0),
        profile=profile(),
        material=material(),
    )

    with pytest.raises(ValueError, match="start or end"):
        straight_to_bent_endpoint_intersection_3d(
            source,
            target(),
            None,
        )
