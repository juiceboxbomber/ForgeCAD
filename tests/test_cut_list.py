"""Tests for ForgeCAD fabrication cut lists."""

import csv
import io

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
    cut_list_to_csv,
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
    assert item.member_name == ""

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


def test_cut_list_item_accepts_member_name():
    member = _member(
        1200.0
    )

    item = cut_list_item_from_member(
        member,
        "M001",
        member_name="Left Lower Rail",
    )

    assert item.member_id == "M001"

    assert (
        item.member_name
        == "Left Lower Rail"
    )


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


def test_build_cut_list_uses_blank_names():
    frame = Frame()

    frame.add_member(
        _member(
            1000.0
        )
    )

    cut_list = build_cut_list(
        frame
    )

    assert (
        cut_list.items[0].member_name
        == ""
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
    assert cut_list.summary_by_profile() == []


def test_summary_groups_members_by_profile():
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

    summary = (
        cut_list.summary_by_profile()
    )

    assert len(summary) == 2

    large = summary[0]
    small = summary[1]

    assert (
        large.tube_profile
        == "1.750 x .120 DOM"
    )

    assert large.piece_count == 2

    assert (
        large.total_length_mm
        == pytest.approx(1500.0)
    )

    assert (
        small.tube_profile
        == "1.000 x .065 DOM"
    )

    assert small.piece_count == 1

    assert (
        small.total_length_mm
        == pytest.approx(750.0)
    )


def test_summary_weight_matches_member_weights():
    frame = Frame()

    member_1 = _member(
        1000.0,
        "1.250 x .095 DOM",
    )

    member_2 = _member(
        500.0,
        "1.250 x .095 DOM",
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

    summary = (
        cut_list.summary_by_profile()
    )

    assert len(summary) == 1

    expected_weight = (
        member_weight_kg(member_1)
        + member_weight_kg(member_2)
    )

    assert (
        summary[0].total_weight_kg
        == pytest.approx(expected_weight)
    )


def test_csv_contains_member_header():
    frame = Frame()

    frame.add_member(
        _member(
            1000.0
        )
    )

    cut_list = build_cut_list(
        frame
    )

    csv_text = cut_list_to_csv(
        cut_list
    )

    assert "Member" in csv_text
    assert "Description" in csv_text
    assert "Tube Profile" in csv_text
    assert "Length (mm)" in csv_text
    assert "Weight (kg)" in csv_text


def test_csv_contains_member_rows():
    frame = Frame()

    frame.add_member(
        _member(
            1000.0,
            "1.000 x .065 DOM",
        )
    )

    cut_list = build_cut_list(
        frame
    )

    csv_text = cut_list_to_csv(
        cut_list
    )

    assert "M001" in csv_text

    assert (
        "1.000 x .065 DOM"
        in csv_text
    )

    assert "1000.000" in csv_text


def test_csv_contains_member_name():
    member = _member(
        1000.0
    )

    item = cut_list_item_from_member(
        member,
        "M001",
        member_name="Front Crossmember",
    )

    from forgecad.services import CutList

    cut_list = CutList(
        items=[
            item
        ]
    )

    csv_text = cut_list_to_csv(
        cut_list
    )

    rows = list(
        csv.reader(
            io.StringIO(csv_text)
        )
    )

    assert rows[0][0] == "Member"
    assert rows[0][1] == "Description"

    assert rows[1][0] == "M001"

    assert (
        rows[1][1]
        == "Front Crossmember"
    )


def test_csv_contains_tube_summary():
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

    cut_list = build_cut_list(
        frame
    )

    csv_text = cut_list_to_csv(
        cut_list
    )

    assert "Tube Summary" in csv_text

    rows = list(
        csv.reader(
            io.StringIO(csv_text)
        )
    )

    summary_rows = [
        row
        for row in rows
        if row
        and row[0]
        == "1.750 x .120 DOM"
        and len(row) == 4
    ]

    assert len(summary_rows) == 1

    assert (
        summary_rows[0][1]
        == "2"
    )

    assert (
        summary_rows[0][2]
        == "1500.000"
    )


def test_csv_contains_overall_totals():
    frame = Frame()

    frame.add_member(
        _member(
            1000.0
        )
    )

    frame.add_member(
        _member(
            500.0
        )
    )

    cut_list = build_cut_list(
        frame
    )

    csv_text = cut_list_to_csv(
        cut_list
    )

    rows = list(
        csv.reader(
            io.StringIO(csv_text)
        )
    )

    totals = [
        row
        for row in rows
        if row
        and row[0] == "Totals"
    ]

    assert len(totals) == 1

    assert totals[0][1] == "2"

    assert (
        totals[0][2]
        == "1500.000"
    )
    