"""Tests for mirroring ForgeCAD geometry across a centerline."""

import pytest

from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services.member_mirror import (
    mirror_member_across_centerline,
    mirror_node_across_centerline,
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


def test_mirror_node_across_vertical_centerline():
    node = Node(
        300.0,
        200.0,
        50.0,
    )

    center_start = Node(
        100.0,
        -1000.0,
        0.0,
    )

    center_end = Node(
        100.0,
        1000.0,
        0.0,
    )

    mirrored = mirror_node_across_centerline(
        node,
        center_start,
        center_end,
    )

    assert mirrored.x == pytest.approx(
        -100.0
    )

    assert mirrored.y == pytest.approx(
        200.0
    )

    assert mirrored.z == pytest.approx(
        50.0
    )


def test_mirror_node_across_horizontal_centerline():
    node = Node(
        400.0,
        300.0,
        25.0,
    )

    center_start = Node(
        -1000.0,
        100.0,
        0.0,
    )

    center_end = Node(
        1000.0,
        100.0,
        0.0,
    )

    mirrored = mirror_node_across_centerline(
        node,
        center_start,
        center_end,
    )

    assert mirrored.x == pytest.approx(
        400.0
    )

    assert mirrored.y == pytest.approx(
        -100.0
    )

    assert mirrored.z == pytest.approx(
        25.0
    )


def test_node_on_centerline_does_not_move():
    node = Node(
        100.0,
        250.0,
        75.0,
    )

    center_start = Node(
        100.0,
        0.0,
        0.0,
    )

    center_end = Node(
        100.0,
        1000.0,
        0.0,
    )

    mirrored = mirror_node_across_centerline(
        node,
        center_start,
        center_end,
    )

    assert mirrored.x == pytest.approx(
        node.x
    )

    assert mirrored.y == pytest.approx(
        node.y
    )

    assert mirrored.z == pytest.approx(
        node.z
    )


def test_diagonal_centerline_reflects_correctly():
    node = Node(
        100.0,
        0.0,
        10.0,
    )

    center_start = Node(
        0.0,
        0.0,
        0.0,
    )

    center_end = Node(
        100.0,
        100.0,
        0.0,
    )

    mirrored = mirror_node_across_centerline(
        node,
        center_start,
        center_end,
    )

    assert mirrored.x == pytest.approx(
        0.0
    )

    assert mirrored.y == pytest.approx(
        100.0
    )

    assert mirrored.z == pytest.approx(
        10.0
    )


def test_member_reflection_preserves_properties():
    profile = make_profile()
    material = make_material()

    member = Member(
        start=Node(
            300.0,
            0.0,
            100.0,
        ),
        end=Node(
            500.0,
            400.0,
            300.0,
        ),
        profile=profile,
        material=material,
    )

    center_start = Node(
        100.0,
        -1000.0,
        0.0,
    )

    center_end = Node(
        100.0,
        1000.0,
        0.0,
    )

    mirrored = mirror_member_across_centerline(
        member,
        center_start,
        center_end,
    )

    assert mirrored.start.x == pytest.approx(
        -100.0
    )

    assert mirrored.start.y == pytest.approx(
        0.0
    )

    assert mirrored.end.x == pytest.approx(
        -300.0
    )

    assert mirrored.end.y == pytest.approx(
        400.0
    )

    assert mirrored.start.z == pytest.approx(
        100.0
    )

    assert mirrored.end.z == pytest.approx(
        300.0
    )

    assert mirrored.profile is profile
    assert mirrored.material is material


def test_three_connected_members_remain_connected_after_mirror():
    profile = make_profile()
    material = make_material()

    a = Node(
        300.0,
        0.0,
        0.0,
    )

    b = Node(
        300.0,
        500.0,
        0.0,
    )

    c = Node(
        500.0,
        750.0,
        0.0,
    )

    d = Node(
        250.0,
        1000.0,
        0.0,
    )

    members = [
        Member(
            start=a,
            end=b,
            profile=profile,
            material=material,
        ),
        Member(
            start=b,
            end=c,
            profile=profile,
            material=material,
        ),
        Member(
            start=c,
            end=d,
            profile=profile,
            material=material,
        ),
    ]

    center_start = Node(
        0.0,
        -1000.0,
        0.0,
    )

    center_end = Node(
        0.0,
        2000.0,
        0.0,
    )

    mirrored = [
        mirror_member_across_centerline(
            member,
            center_start,
            center_end,
        )
        for member in members
    ]

    assert len(
        mirrored
    ) == 3

    assert (
        mirrored[0].end
        == mirrored[1].start
    )

    assert (
        mirrored[1].end
        == mirrored[2].start
    )

    assert mirrored[0].start.x == pytest.approx(
        -300.0
    )

    assert mirrored[1].end.x == pytest.approx(
        -500.0
    )

    assert mirrored[2].end.x == pytest.approx(
        -250.0
    )


def test_zero_length_centerline_is_rejected():
    node = Node(
        100.0,
        200.0,
        0.0,
    )

    center = Node(
        0.0,
        0.0,
        0.0,
    )

    with pytest.raises(
        ValueError,
        match="centerline",
    ):
        mirror_node_across_centerline(
            node,
            center,
            center,
        )
        