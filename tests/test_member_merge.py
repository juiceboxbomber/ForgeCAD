"""Tests for safe merging of collinear ForgeCAD members."""

from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services.member_merge import (
    merge_collinear_members,
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


def member(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=profile(),
        material=material(),
    )


def test_opposite_collinear_members_merge():
    first = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            -500.0,
            0.0,
            0.0,
        ),
    )

    merged = merge_collinear_members(
        first,
        second,
    )

    assert merged is not None

    assert merged.start == Node(
        500.0,
        0.0,
        0.0,
    )

    assert merged.end == Node(
        -500.0,
        0.0,
        0.0,
    )


def test_angled_members_do_not_merge():
    first = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            500.0,
            0.0,
            200.0,
        ),
    )

    second = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            -500.0,
            0.0,
            200.0,
        ),
    )

    assert (
        merge_collinear_members(
            first,
            second,
        )
        is None
    )


def test_members_without_shared_endpoint_do_not_merge():
    first = member(
        Node(
            100.0,
            0.0,
            0.0,
        ),
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        Node(
            -100.0,
            0.0,
            0.0,
        ),
        Node(
            -500.0,
            0.0,
            0.0,
        ),
    )

    assert (
        merge_collinear_members(
            first,
            second,
        )
        is None
    )


def test_same_direction_members_do_not_merge():
    first = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            250.0,
            0.0,
            0.0,
        ),
    )

    assert (
        merge_collinear_members(
            first,
            second,
        )
        is None
    )


def test_reversed_endpoint_order_can_merge():
    first = member(
        Node(
            500.0,
            0.0,
            0.0,
        ),
        Node(
            0.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            -500.0,
            0.0,
            0.0,
        ),
    )

    merged = merge_collinear_members(
        first,
        second,
    )

    assert merged is not None

    assert merged.start == Node(
        500.0,
        0.0,
        0.0,
    )

    assert merged.end == Node(
        -500.0,
        0.0,
        0.0,
    )


def test_real_mirror_coordinates_merge_despite_tiny_numeric_drift():
    first = member(
        Node(
            427.0589848792515,
            -330.93868852189246,
            0.0,
        ),
        Node(
            0.0,
            -330.939,
            0.0,
        ),
    )

    second = member(
        Node(
            -427.0589848792515,
            -330.93868852189246,
            0.0,
        ),
        Node(
            0.0,
            -330.939,
            0.0,
        ),
    )

    merged = merge_collinear_members(
        first,
        second,
    )

    assert merged is not None

    assert merged.start == Node(
        427.0589848792515,
        -330.93868852189246,
        0.0,
    )

    assert merged.end == Node(
        -427.0589848792515,
        -330.93868852189246,
        0.0,
    )
