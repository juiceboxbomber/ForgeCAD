"""Tests for member and tube-profile behavior."""

import pytest

from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services import (
    create_default_tube_library,
)


def _default_material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def test_default_tube_library_contains_expected_profiles():
    library = create_default_tube_library()

    assert library.names == (
        "1.000 x .065 DOM",
        "1.250 x .095 DOM",
        "1.750 x .120 DOM",
    )


def test_default_tube_library_active_profile_is_1750_dom():
    library = create_default_tube_library()

    assert library.active_name == "1.750 x .120 DOM"

    profile = library.active_profile

    assert profile.outside_diameter == pytest.approx(44.45)
    assert profile.wall_thickness == pytest.approx(3.048)


def test_member_uses_selected_profile_without_changing_geometry():
    library = create_default_tube_library()

    start = Node(0, 0, 0)
    end = Node(1000, 0, 0)

    profile = library.get(
        "1.250 x .095 DOM"
    )

    member = Member(
        start=start,
        end=end,
        profile=profile,
        material=_default_material(),
    )

    assert member.length == pytest.approx(1000.0)
    assert member.profile is profile
    assert member.profile.outside_diameter == pytest.approx(31.75)
    assert member.profile.wall_thickness == pytest.approx(2.413)


def test_different_profile_keeps_same_member_length():
    library = create_default_tube_library()

    start = Node(0, 0, 0)
    end = Node(750, 250, 0)

    material = _default_material()

    small_member = Member(
        start=start,
        end=end,
        profile=library.get(
            "1.000 x .065 DOM"
        ),
        material=material,
    )

    large_member = Member(
        start=start,
        end=end,
        profile=library.get(
            "1.750 x .120 DOM"
        ),
        material=material,
    )

    assert small_member.length == pytest.approx(
        large_member.length
    )

    assert (
        small_member.profile.outside_diameter
        < large_member.profile.outside_diameter
    )


def test_tube_inside_diameter_changes_with_profile():
    library = create_default_tube_library()

    small = library.get(
        "1.000 x .065 DOM"
    )

    large = library.get(
        "1.750 x .120 DOM"
    )

    assert small.inside_diameter == pytest.approx(
        25.4 - (2 * 1.651)
    )

    assert large.inside_diameter == pytest.approx(
        44.45 - (2 * 3.048)
    )


def test_member_is_immutable():
    library = create_default_tube_library()

    member = Member(
        start=Node(0, 0, 0),
        end=Node(500, 0, 0),
        profile=library.active_profile,
        material=_default_material(),
    )

    with pytest.raises(Exception):
        member.profile = library.get(
            "1.000 x .065 DOM"
        )
        