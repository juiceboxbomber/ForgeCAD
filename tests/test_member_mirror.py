"""Tests for ForgeCAD member mirror geometry."""

from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services.member_mirror import (
    member_is_on_y_zero,
    mirror_member_across_y_zero,
    mirror_members_across_y_zero,
    mirror_node_across_y_zero,
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


def test_mirror_node_changes_only_y():
    node = Node(
        500.0,
        300.0,
        400.0,
    )

    mirrored = (
        mirror_node_across_y_zero(
            node
        )
    )

    assert mirrored.x == 500.0
    assert mirrored.y == -300.0
    assert mirrored.z == 400.0


def test_negative_y_mirrors_positive():
    node = Node(
        125.0,
        -275.0,
        50.0,
    )

    mirrored = (
        mirror_node_across_y_zero(
            node
        )
    )

    assert mirrored.x == 125.0
    assert mirrored.y == 275.0
    assert mirrored.z == 50.0


def test_centerline_node_remains_on_centerline():
    node = Node(
        1000.0,
        0.0,
        250.0,
    )

    mirrored = (
        mirror_node_across_y_zero(
            node
        )
    )

    assert mirrored.x == 1000.0
    assert mirrored.y == 0.0
    assert mirrored.z == 250.0


def test_mirror_member_mirrors_both_endpoints():
    profile = make_profile()
    material = make_material()

    member = Member(
        start=Node(
            0.0,
            300.0,
            100.0,
        ),
        end=Node(
            500.0,
            450.0,
            400.0,
        ),
        profile=profile,
        material=material,
    )

    mirrored = (
        mirror_member_across_y_zero(
            member
        )
    )

    assert mirrored.start == Node(
        0.0,
        -300.0,
        100.0,
    )

    assert mirrored.end == Node(
        500.0,
        -450.0,
        400.0,
    )


def test_mirror_member_preserves_profile():
    profile = make_profile()

    member = Member(
        start=Node(
            0.0,
            200.0,
            0.0,
        ),
        end=Node(
            500.0,
            200.0,
            0.0,
        ),
        profile=profile,
        material=make_material(),
    )

    mirrored = (
        mirror_member_across_y_zero(
            member
        )
    )

    assert mirrored.profile == profile


def test_mirror_member_preserves_material():
    material = make_material()

    member = Member(
        start=Node(
            0.0,
            200.0,
            0.0,
        ),
        end=Node(
            500.0,
            200.0,
            0.0,
        ),
        profile=make_profile(),
        material=material,
    )

    mirrored = (
        mirror_member_across_y_zero(
            member
        )
    )

    assert mirrored.material == material


def test_double_mirror_restores_original_geometry():
    member = Member(
        start=Node(
            100.0,
            250.0,
            50.0,
        ),
        end=Node(
            700.0,
            400.0,
            325.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )

    mirrored = (
        mirror_member_across_y_zero(
            member
        )
    )

    restored = (
        mirror_member_across_y_zero(
            mirrored
        )
    )

    assert restored.start == member.start
    assert restored.end == member.end


def test_centerline_member_is_recognized():
    member = Member(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            500.0,
            0.0,
            300.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )

    assert member_is_on_y_zero(
        member
    )


def test_member_crossing_centerline_is_not_centerline_member():
    member = Member(
        start=Node(
            0.0,
            -300.0,
            0.0,
        ),
        end=Node(
            0.0,
            300.0,
            0.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )

    assert not member_is_on_y_zero(
        member
    )


def test_batch_mirror_skips_centerline_members():
    side_member = Member(
        start=Node(
            0.0,
            300.0,
            0.0,
        ),
        end=Node(
            500.0,
            300.0,
            0.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )

    center_member = Member(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            500.0,
            0.0,
            0.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )

    mirrored = (
        mirror_members_across_y_zero(
            [
                side_member,
                center_member,
            ]
        )
    )

    assert len(
        mirrored
    ) == 1

    assert mirrored[
        0
    ].start.y == -300.0

    assert mirrored[
        0
    ].end.y == -300.0
    