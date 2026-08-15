"""Tests for ForgeCAD bent structural members."""

import pytest

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Material,
    Node,
    StraightRun,
    TubeProfile,
)

from forgecad.geometry import Vector3D


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


def _tube():
    return BentTube(
        straight_runs=(
            StraightRun(
                500.0
            ),
            StraightRun(
                750.0
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


def test_bent_member_owns_start_and_end_nodes():
    start = Node(
        0.0,
        0.0,
        0.0,
    )

    end = Node(
        600.0,
        850.0,
        0.0,
    )

    member = BentMember(
        start=start,
        end=end,
        tube=_tube(),
    )

    assert member.start is start
    assert member.end is end


def test_bent_member_exposes_tube_profile():
    tube = _tube()

    member = BentMember(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            600.0,
            850.0,
            0.0,
        ),
        tube=tube,
    )

    assert member.profile is tube.profile


def test_bent_member_exposes_tube_material():
    tube = _tube()

    member = BentMember(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            600.0,
            850.0,
            0.0,
        ),
        tube=tube,
    )

    assert member.material is tube.material


def test_bent_member_length_is_developed_tube_length():
    tube = _tube()

    member = BentMember(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            600.0,
            850.0,
            0.0,
        ),
        tube=tube,
    )

    assert member.length == pytest.approx(
        tube.developed_length
    )


def test_bent_member_has_default_path_orientation():
    member = BentMember(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            600.0,
            850.0,
            0.0,
        ),
        tube=_tube(),
    )

    assert member.initial_direction == Vector3D(
        1.0,
        0.0,
        0.0,
    )

    assert member.initial_bend_normal == Vector3D(
        0.0,
        0.0,
        1.0,
    )


def test_bent_member_normalizes_orientation_vectors():
    member = BentMember(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            600.0,
            850.0,
            0.0,
        ),
        tube=_tube(),
        initial_direction=Vector3D(
            10.0,
            0.0,
            0.0,
        ),
        initial_bend_normal=Vector3D(
            0.0,
            0.0,
            5.0,
        ),
    )

    assert member.initial_direction == Vector3D(
        1.0,
        0.0,
        0.0,
    )

    assert member.initial_bend_normal == Vector3D(
        0.0,
        0.0,
        1.0,
    )


def test_bent_member_rejects_nonperpendicular_orientation():
    with pytest.raises(
        ValueError,
        match="perpendicular",
    ):
        BentMember(
            start=Node(
                0.0,
                0.0,
                0.0,
            ),
            end=Node(
                600.0,
                850.0,
                0.0,
            ),
            tube=_tube(),
            initial_direction=Vector3D(
                1.0,
                0.0,
                0.0,
            ),
            initial_bend_normal=Vector3D(
                1.0,
                0.0,
                1.0,
            ),
    )

    