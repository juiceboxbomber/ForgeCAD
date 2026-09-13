"""Tests for ForgeCAD straight-member splitting."""

import pytest

from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services.member_split import (
    projected_point_on_member,
    split_member,
    validate_split_point,
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


def make_member():
    return Member(
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
        profile=make_profile(),
        material=make_material(),
    )


def test_midpoint_split_creates_two_members():
    member = make_member()

    first, second = split_member(
        member,
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    assert first.start == Node(
        0.0,
        0.0,
        0.0,
    )

    assert first.end == Node(
        500.0,
        0.0,
        0.0,
    )

    assert second.start == Node(
        500.0,
        0.0,
        0.0,
    )

    assert second.end == Node(
        1000.0,
        0.0,
        0.0,
    )


def test_split_members_share_exact_split_node():
    member = make_member()

    first, second = split_member(
        member,
        Node(
            250.0,
            0.0,
            0.0,
        ),
    )

    assert (
        first.end
        == second.start
    )


def test_split_preserves_profile():
    member = make_member()

    first, second = split_member(
        member,
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    assert first.profile is member.profile
    assert second.profile is member.profile


def test_split_preserves_material():
    member = make_member()

    first, second = split_member(
        member,
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    assert first.material is member.material
    assert second.material is member.material


def test_split_works_on_3d_member():
    member = Member(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            1000.0,
            500.0,
            250.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )

    first, second = split_member(
        member,
        Node(
            500.0,
            250.0,
            125.0,
        ),
    )

    assert first.end == Node(
        500.0,
        250.0,
        125.0,
    )

    assert second.start == first.end


def test_off_centerline_point_is_rejected():
    member = make_member()

    with pytest.raises(
        ValueError,
        match="centerline",
    ):
        split_member(
            member,
            Node(
                500.0,
                10.0,
                0.0,
            ),
        )


def test_start_endpoint_is_rejected():
    member = make_member()

    with pytest.raises(
        ValueError,
        match="endpoint",
    ):
        split_member(
            member,
            member.start,
        )


def test_end_endpoint_is_rejected():
    member = make_member()

    with pytest.raises(
        ValueError,
        match="endpoint",
    ):
        split_member(
            member,
            member.end,
        )


def test_point_beyond_member_is_rejected():
    member = make_member()

    with pytest.raises(
        ValueError,
        match="endpoint",
    ):
        split_member(
            member,
            Node(
                1500.0,
                0.0,
                0.0,
            ),
        )


def test_projection_returns_exact_centerline_point():
    member = make_member()

    projected = (
        projected_point_on_member(
            member,
            Node(
                400.0,
                20.0,
                0.0,
            ),
        )
    )

    assert projected == Node(
        400.0,
        0.0,
        0.0,
    )


def test_validate_split_point_returns_canonical_node():
    member = make_member()

    point = validate_split_point(
        member,
        Node(
            750.0,
            0.0,
            0.0,
        ),
    )

    assert point == Node(
        750.0,
        0.0,
        0.0,
    )
    