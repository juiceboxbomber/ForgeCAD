"""Tests for ForgeCAD tube stock planning."""

from types import SimpleNamespace

import pytest

from forgecad.services.tube_stock import (
    DEFAULT_SAW_KERF_MM,
    DEFAULT_STOCK_LENGTH_MM,
    plan_tube_stock,
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


def test_default_stock_is_twenty_feet():
    assert (
        DEFAULT_STOCK_LENGTH_MM
        == 6096.0
    )


def test_default_saw_kerf_is_one_eighth_inch():
    assert (
        DEFAULT_SAW_KERF_MM
        == pytest.approx(
            3.175
        )
    )


def test_empty_cut_list_produces_empty_plan():
    plan = plan_tube_stock(
        _cut_list()
    )

    assert plan.profile_count == 0
    assert plan.stick_count == 0
    assert plan.piece_count == 0
    assert plan.total_drop_length_mm == 0.0


def test_two_pieces_fit_on_one_stock_stick():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "M001",
                3000.0,
            ),
            _item(
                "M002",
                2500.0,
            ),
        )
    )

    assert plan.profile_count == 1

    profile = plan.profile_plans[0]

    assert profile.stick_count == 1

    stick = profile.sticks[0]

    assert [
        piece.member_id
        for piece in stick.pieces
    ] == [
        "M001",
        "M002",
    ]

    assert (
        stick.piece_length_mm
        == pytest.approx(
            5500.0
        )
    )

    assert (
        stick.kerf_loss_mm
        == pytest.approx(
            2 * 3.175
        )
    )

    assert (
        stick.drop_length_mm
        == pytest.approx(
            6096.0
            - 5500.0
            - 2 * 3.175
        )
    )


def test_pieces_that_do_not_fit_use_multiple_sticks():
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
        saw_kerf_mm=0.0,
    )

    assert (
        plan.stick_count
        == 2
    )


def test_best_fit_decreasing_packs_common_case_into_two_sticks():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "M001",
                3500.0,
            ),
            _item(
                "M002",
                2600.0,
            ),
            _item(
                "M003",
                3400.0,
            ),
            _item(
                "M004",
                2500.0,
            ),
        ),
        saw_kerf_mm=0.0,
    )

    assert (
        plan.stick_count
        == 2
    )

    used_lengths = sorted(
        stick.used_length_mm
        for stick
        in plan.profile_plans[
            0
        ].sticks
    )

    assert used_lengths == [
        6000.0,
        6000.0,
    ]


def test_different_profiles_never_share_stock():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "M001",
                1000.0,
                profile=(
                    "1.750 x .120 DOM"
                ),
            ),
            _item(
                "M002",
                1000.0,
                profile=(
                    "1.500 x .120 DOM"
                ),
            ),
        )
    )

    assert (
        plan.profile_count
        == 2
    )

    assert [
        item.tube_profile
        for item
        in plan.profile_plans
    ] == [
        "1.750 x .120 DOM",
        "1.500 x .120 DOM",
    ]


def test_same_profile_different_materials_do_not_mix():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "M001",
                1000.0,
                material=(
                    "A513 Type 5 DOM"
                ),
            ),
            _item(
                "M002",
                1000.0,
                material=(
                    "4130 Chromoly"
                ),
            ),
        )
    )

    assert (
        plan.profile_count
        == 2
    )

    assert {
        profile.material
        for profile
        in plan.profile_plans
    } == {
        "A513 Type 5 DOM",
        "4130 Chromoly",
    }


def test_bent_tube_name_is_preserved_as_piece_label():
    plan = plan_tube_stock(
        _cut_list(
            _item(
                "ForgeCADBentTube",
                2200.0,
                member_name=(
                    "Main Hoop"
                ),
            ),
        )
    )

    piece = (
        plan.profile_plans[
            0
        ]
        .sticks[
            0
        ]
        .pieces[
            0
        ]
    )

    assert (
        piece.display_name
        == "Main Hoop"
    )


def test_total_accounting_matches_stock_balance():
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
            _item(
                "ForgeCADBentTube",
                2200.0,
                member_name=(
                    "Main Hoop"
                ),
            ),
        )
    )

    assert (
        plan.total_stock_length_mm
        == pytest.approx(
            plan.total_piece_length_mm
            + plan.total_kerf_loss_mm
            + plan.total_drop_length_mm
        )
    )


def test_piece_longer_than_stock_raises_clear_error():
    with pytest.raises(
        ValueError,
        match="exceeds",
    ):
        plan_tube_stock(
            _cut_list(
                _item(
                    "M001",
                    6100.0,
                ),
            )
        )


@pytest.mark.parametrize(
    (
        "stock_length_mm",
        "saw_kerf_mm",
    ),
    [
        (0.0, 3.175),
        (-1.0, 3.175),
        (6096.0, -0.1),
    ],
)
def test_invalid_planning_dimensions_are_rejected(
    stock_length_mm,
    saw_kerf_mm,
):
    with pytest.raises(
        ValueError
    ):
        plan_tube_stock(
            _cut_list(
                _item(
                    "M001",
                    1000.0,
                ),
            ),
            stock_length_mm=(
                stock_length_mm
            ),
            saw_kerf_mm=(
                saw_kerf_mm
            ),
        )
