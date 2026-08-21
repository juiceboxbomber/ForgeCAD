"""Tests for mirroring ForgeCAD geometry across principal planes."""

import pytest

from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services.member_mirror import (
    mirror_member_across_plane,
    mirror_node_across_plane,
)


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def make_material():
    return Material(
        name="DOM Steel",
        density=7850.0,
        yield_strength=350.0,
    )


@pytest.mark.parametrize(
    (
        "plane",
        "expected",
    ),
    [
        (
            "XY",
            (
                100.0,
                200.0,
                -300.0,
            ),
        ),
        (
            "XZ",
            (
                100.0,
                -200.0,
                300.0,
            ),
        ),
        (
            "YZ",
            (
                -100.0,
                200.0,
                300.0,
            ),
        ),
    ],
)
def test_mirror_node_across_principal_plane(
    plane,
    expected,
):
    node = Node(
        100.0,
        200.0,
        300.0,
    )

    mirrored = mirror_node_across_plane(
        node,
        plane,
    )

    assert mirrored.x == pytest.approx(
        expected[0]
    )

    assert mirrored.y == pytest.approx(
        expected[1]
    )

    assert mirrored.z == pytest.approx(
        expected[2]
    )


@pytest.mark.parametrize(
    "plane",
    [
        "XY",
        "XZ",
        "YZ",
    ],
)
def test_double_plane_mirror_restores_node(
    plane,
):
    node = Node(
        125.0,
        -275.0,
        450.0,
    )

    mirrored = mirror_node_across_plane(
        node,
        plane,
    )

    restored = mirror_node_across_plane(
        mirrored,
        plane,
    )

    assert restored == node


def test_plane_mirror_preserves_member_properties():
    profile = make_profile()
    material = make_material()

    member = Member(
        start=Node(
            100.0,
            200.0,
            300.0,
        ),
        end=Node(
            500.0,
            600.0,
            700.0,
        ),
        profile=profile,
        material=material,
    )

    mirrored = mirror_member_across_plane(
        member,
        "XZ",
    )

    assert mirrored.start == Node(
        100.0,
        -200.0,
        300.0,
    )

    assert mirrored.end == Node(
        500.0,
        -600.0,
        700.0,
    )

    assert mirrored.profile is profile
    assert mirrored.material is material


def test_plane_name_is_case_insensitive():
    node = Node(
        100.0,
        200.0,
        300.0,
    )

    assert (
        mirror_node_across_plane(
            node,
            "xz",
        )
        == Node(
            100.0,
            -200.0,
            300.0,
        )
    )


def test_unknown_plane_is_rejected():
    with pytest.raises(
        ValueError,
        match="plane",
    ):
        mirror_node_across_plane(
            Node(
                100.0,
                200.0,
                300.0,
            ),
            "AB",
        )
        