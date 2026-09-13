"""Tests for ForgeCAD tube stock plan CSV export."""

import csv
import io
from types import SimpleNamespace

from forgecad.services.tube_stock import (
    plan_tube_stock,
)
from forgecad.services.tube_stock_export import (
    tube_stock_plan_to_csv,
)


def _item(
    member_id,
    length_mm,
    profile="1.750 x .120 DOM",
    material="A513 Type 5 DOM",
    member_name="",
):
    return SimpleNamespace(
        member_id=member_id,
        member_name=member_name,
        tube_profile=profile,
        material=material,
        length_mm=length_mm,
    )


def _cut_list(*items):
    return SimpleNamespace(
        items=list(items)
    )


def _rows(csv_text):
    return list(
        csv.reader(
            io.StringIO(csv_text)
        )
    )


def test_csv_contains_shop_cut_header():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "M001",
                1000.0,
            )
        )
    )

    rows = _rows(
        tube_stock_plan_to_csv(plan)
    )

    assert rows[0] == [
        "Tube Profile",
        "Material",
        "Stock Stick",
        "Cut Order",
        "Member",
        "Description",
        "Finished Cut Length (mm)",
        "Kerf Allowance (mm)",
        "Remaining Stock (mm)",
    ]


def test_csv_exports_cut_sequence_and_remaining_stock():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "M001",
                1800.0,
            ),
            _item(
                "M002",
                1500.0,
            ),
        ),
        stock_length_mm=4000.0,
        saw_kerf_mm=3.0,
    )

    rows = _rows(
        tube_stock_plan_to_csv(plan)
    )

    assert rows[1][2] == "1"
    assert rows[1][3] == "1"
    assert rows[1][4] == "M001"
    assert rows[1][6] == "1800.000"
    assert rows[1][7] == "3.000"
    assert rows[1][8] == "2197.000"

    assert rows[2][2] == "1"
    assert rows[2][3] == "2"
    assert rows[2][4] == "M002"
    assert rows[2][8] == "694.000"


def test_csv_preserves_bent_tube_description():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "ForgeCADBentTube",
                2200.0,
                member_name="Main Hoop",
            )
        )
    )

    rows = _rows(
        tube_stock_plan_to_csv(plan)
    )

    assert rows[1][4] == "ForgeCADBentTube"
    assert rows[1][5] == "Main Hoop"


def test_csv_keeps_profiles_and_materials_separate():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "M001",
                1000.0,
                profile="1.750 x .120 DOM",
                material="A513 Type 5 DOM",
            ),
            _item(
                "M002",
                1000.0,
                profile="1.500 x .120 DOM",
                material="4130 Chromoly",
            ),
        )
    )

    rows = _rows(
        tube_stock_plan_to_csv(plan)
    )

    data_rows = [
        row
        for row in rows
        if row
        and row[0] not in (
            "Totals",
            "Tube Profile",
        )
    ]

    assert {
        (
            row[0],
            row[1],
        )
        for row in data_rows
    } == {
        (
            "1.750 x .120 DOM",
            "A513 Type 5 DOM",
        ),
        (
            "1.500 x .120 DOM",
            "4130 Chromoly",
        ),
    }


def test_csv_contains_stock_totals():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "M001",
                4000.0,
            ),
            _item(
                "M002",
                2500.0,
            ),
        ),
        stock_length_mm=6096.0,
        saw_kerf_mm=0.0,
    )

    rows = _rows(
        tube_stock_plan_to_csv(plan)
    )

    totals_header = [
        "Totals",
        "Sticks Purchased",
        "Finished Tube Length (mm)",
        "Kerf Loss (mm)",
        "Drop (mm)",
        "Purchased Stock Length (mm)",
    ]

    totals_header_index = rows.index(
        totals_header
    )

    totals = rows[
        totals_header_index + 1
    ]

    assert totals[0] == "Totals"
    assert totals[1] == "2"
    assert totals[2] == "6500.000"
    assert totals[3] == "0.000"
    assert totals[4] == "5692.000"
    assert totals[5] == "12192.000"


def test_csv_quotes_commas_in_piece_description():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "M001",
                1000.0,
                member_name="Main Hoop, Left",
            )
        )
    )

    csv_text = tube_stock_plan_to_csv(
        plan
    )

    assert (
        '"Main Hoop, Left"'
        in csv_text
    )

    rows = _rows(
        csv_text
    )

    assert (
        rows[1][5]
        == "Main Hoop, Left"
    )


def test_empty_plan_exports_header_and_zero_totals():
    plan = plan_tube_stock(
        _cut_list()
    )

    rows = _rows(
        tube_stock_plan_to_csv(plan)
    )

    assert rows[0][0] == "Tube Profile"

    totals = rows[-1]

    assert totals == [
        "Totals",
        "0",
        "0.000",
        "0.000",
        "0.000",
        "0.000",
    ]
