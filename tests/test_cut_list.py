"""Tests for ForgeCAD fabrication cut lists."""

import pytest

from forgecad.fabrication import (
    Frame,
    Material,
    Member,
    Node,
)
from forgecad.services import (
    build_cut_list,
    create_default_tube_library,
    cut_list_item_from_member,
    member_weight_kg,
    profile_name_for_member,
)


def _material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def _member(
    length,
    profile_name="1.750 x .120 DOM",
):
    library = create_default_tube_library()

    return Member(
        start=Node(
            0,
            0,
            0,
        ),
        end=Node(
            length,
            0,
            0,
        ),
        profile=library.get(
            profile_name
        ),
        material=_material(),
    )


def test_profile_name_is_resolved_from_library():
    member = _member(
        1000.0,
        "1.250 x .095 DOM",
    )

    assert (
        profile_name_for_member(member)
        == "1.250 x .095 DOM"
    )


def test_member_weight_is_positive():
    member = _member(
        1000.0
    )

    weight = member_weight_kg(
        member
    )

    assert weight > 0


def test_longer_member_weighs_more():
    short_member = _member(
        500.0
    )

    long_member = _member(
        1000.0
    )

    assert (
        member_weight_kg(long_member)
        == pytest.approx(
            member_weight_kg(short_member)
            * 2.0
        )
    )


def test_cut_list_item_contains_member_data():
    member = _member(
        1200.0,
        "1.000 x .065 DOM",
    )

    item = cut_list_item_from_member(
        member,
        "M007",
    )

    assert item.member_id == "M007"

    assert (
        item.tube_profile
        == "1.000 x .065 DOM"
    )

    assert (
        item.material
        == "A513 Type 5 DOM"
    )

    assert item.length_mm == pytest.approx(
        1200.0
    )

    assert (
        item.outside_diameter_mm
        == pytest.approx(25.4)
    )

    assert (
        item.wall_thickness_mm
        == pytest.approx(1.651)
    )

    assert item.weight_kg > 0


def test_build_cut_list_assigns_member_ids():
    frame = Frame()

    frame.add_member(
        _member(
            1000.0
        )
    )

    frame.add_member(
        _member(
            750.0
        )
    )

    cut_list = build_cut_list(
        frame
    )

    assert cut_list.member_count == 2

    assert (
        cut_list.items[0].member_id
        == "M001"
    )

    assert (
        cut_list.items[1].member_id
        == "M002"
    )


def test_cut_list_total_length():
    frame = Frame()

    frame.add_member(
        _member(
            1000.0
        )
    )

    frame.add_member(
        _member(
            750.0
        )
    )

    frame.add_member(
        _member(
            250.0
        )
    )

    cut_list = build_cut_list(
        frame
    )

    assert (
        cut_list.total_length_mm
        == pytest.approx(2000.0)
    )


def test_cut_list_total_weight():
    frame = Frame()

    member_1 = _member(
        1000.0
    )

    member_2 = _member(
        500.0
    )

    frame.add_member(
        member_1
    )

    frame.add_member(
        member_2
    )

    cut_list = build_cut_list(
        frame
    )

    expected = (
        member_weight_kg(member_1)
        + member_weight_kg(member_2)
    )

    assert (
        cut_list.total_weight_kg
        == pytest.approx(expected)
    )


def test_cut_list_length_by_profile():
    frame = Frame()

    frame.add_member(
        _member(
            1000.0,
            "1.750 x .120 DOM",
        )
    )

    frame.add_member(
        _member(
            500.0,
            "1.750 x .120 DOM",
        )
    )

    frame.add_member(
        _member(
            750.0,
            "1.000 x .065 DOM",
        )
    )

    cut_list = build_cut_list(
        frame
    )

    totals = (
        cut_list.length_by_profile()
    )

    assert totals[
        "1.750 x .120 DOM"
    ] == pytest.approx(
        1500.0
    )

    assert totals[
        "1.000 x .065 DOM"
    ] == pytest.approx(
        750.0
    )


def test_cut_list_count_by_profile():
    frame = Frame()

    frame.add_member(
        _member(
            1000.0,
            "1.750 x .120 DOM",
        )
    )

    frame.add_member(
        _member(
            500.0,
            "1.750 x .120 DOM",
        )
    )

    frame.add_member(
        _member(
            750.0,
            "1.250 x .095 DOM",
        )
    )

    cut_list = build_cut_list(
        frame
    )

    counts = (
        cut_list.count_by_profile()
    )

    assert counts[
        "1.750 x .120 DOM"
    ] == 2

    assert counts[
        "1.250 x .095 DOM"
    ] == 1


def test_empty_frame_produces_empty_cut_list():
    cut_list = build_cut_list(
        Frame()
    )

    assert cut_list.member_count == 0

    assert cut_list.total_length_mm == 0

    assert cut_list.total_weight_kg == 0

    assert cut_list.length_by_profile() == {}

    assert cut_list.count_by_profile() == {}
    