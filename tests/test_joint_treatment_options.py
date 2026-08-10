"""Tests for Joint Inspector treatment options."""

import sys
import types


# ---------------------------------------------------------
# Minimal FreeCAD / Part stubs
# ---------------------------------------------------------

sys.modules[
    "FreeCAD"
] = types.ModuleType(
    "FreeCAD"
)

sys.modules[
    "FreeCADGui"
] = types.ModuleType(
    "FreeCADGui"
)

sys.modules[
    "Part"
] = types.ModuleType(
    "Part"
)


from forgecad.fabrication.joint_treatment import (
    JointTreatmentMode,
)
from forgecad.adapters.freecad.joint_treatment_options import (
    member_display_name,
    member_layout_id,
    option_matches_saved_treatment,
    selected_option_index,
    treatment_options_for_members,
)


class FakeMember:
    """Minimal generated ForgeCAD member."""

    def __init__(
        self,
        member_id,
        layout_id,
        member_name="",
    ):
        self.MemberID = member_id
        self.MemberName = member_name
        self.SourceLayoutID = layout_id


def test_member_display_name_uses_id():
    member = FakeMember(
        "M001",
        "L001",
    )

    assert (
        member_display_name(
            member
        )
        == "M001"
    )


def test_member_display_name_includes_name():
    member = FakeMember(
        "M001",
        "L001",
        "Front Rail",
    )

    assert (
        member_display_name(
            member
        )
        == "M001 - Front Rail"
    )


def test_member_layout_id_returns_source_identity():
    member = FakeMember(
        "M001",
        "L042",
    )

    assert (
        member_layout_id(
            member
        )
        == "L042"
    )


def test_corner_has_four_treatment_options():
    first = FakeMember(
        "M001",
        "L001",
    )

    second = FakeMember(
        "M002",
        "L002",
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
        )
    )

    assert len(
        options
    ) == 4

    assert options[
        0
    ].mode == (
        JointTreatmentMode.AUTO
    )

    assert options[
        1
    ].mode == (
        JointTreatmentMode.MEMBER_THROUGH
    )

    assert options[
        1
    ].through_layout_ids == (
        "L001",
    )

    assert options[
        2
    ].through_layout_ids == (
        "L002",
    )

    assert options[
        3
    ].mode == (
        JointTreatmentMode.BOTH_COPED
    )


def test_corner_labels_identify_through_members():
    first = FakeMember(
        "M001",
        "L001",
        "Rail",
    )

    second = FakeMember(
        "M002",
        "L002",
        "Crossmember",
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
        )
    )

    assert options[
        1
    ].label == (
        "M001 - Rail Through"
    )

    assert options[
        2
    ].label == (
        "M002 - Crossmember Through"
    )

    assert options[
        3
    ].label == (
        "Both Coped"
    )


def test_t_joint_has_single_and_pair_options():
    first = FakeMember(
        "M001",
        "L001",
    )

    second = FakeMember(
        "M002",
        "L002",
    )

    third = FakeMember(
        "M003",
        "L003",
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
                third,
            ]
        )
    )

    # Automatic
    # 3 individual-through choices
    # 3 possible through pairs
    assert len(
        options
    ) == 7

    pair_options = [
        option
        for option in options
        if (
            option.mode
            == JointTreatmentMode.THROUGH_PAIR
        )
    ]

    assert len(
        pair_options
    ) == 3


def test_t_joint_pair_ids_are_persistent_layout_ids():
    members = [
        FakeMember(
            "M001",
            "L001",
        ),
        FakeMember(
            "M002",
            "L002",
        ),
        FakeMember(
            "M003",
            "L003",
        ),
    ]

    options = (
        treatment_options_for_members(
            members
        )
    )

    pair_ids = {
        option.through_layout_ids
        for option in options
        if (
            option.mode
            == JointTreatmentMode.THROUGH_PAIR
        )
    }

    assert pair_ids == {
        (
            "L001",
            "L002",
        ),
        (
            "L001",
            "L003",
        ),
        (
            "L002",
            "L003",
        ),
    }


def test_member_without_layout_id_is_not_manual_choice():
    first = FakeMember(
        "M001",
        "",
    )

    second = FakeMember(
        "M002",
        "L002",
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
        )
    )

    manual_ids = {
        option.through_layout_ids
        for option in options
        if (
            option.mode
            == JointTreatmentMode.MEMBER_THROUGH
        )
    }

    assert manual_ids == {
        (
            "L002",
        )
    }


def test_saved_member_through_matches_option():
    member = FakeMember(
        "M001",
        "L001",
    )

    options = (
        treatment_options_for_members(
            [
                member,
                FakeMember(
                    "M002",
                    "L002",
                ),
            ]
        )
    )

    assert option_matches_saved_treatment(
        options[
            1
        ],
        "member_through",
        (
            "L001",
        ),
    )


def test_saved_treatment_selects_correct_option():
    members = [
        FakeMember(
            "M001",
            "L001",
        ),
        FakeMember(
            "M002",
            "L002",
        ),
    ]

    options = (
        treatment_options_for_members(
            members
        )
    )

    index = selected_option_index(
        options,
        (
            "member_through",
            (
                "L002",
            ),
        ),
    )

    assert (
        options[
            index
        ].through_layout_ids
        == (
            "L002",
        )
    )


def test_missing_saved_treatment_selects_automatic():
    members = [
        FakeMember(
            "M001",
            "L001",
        ),
        FakeMember(
            "M002",
            "L002",
        ),
    ]

    options = (
        treatment_options_for_members(
            members
        )
    )

    assert (
        selected_option_index(
            options,
            None,
        )
        == 0
    )


def test_stale_saved_treatment_selects_automatic():
    members = [
        FakeMember(
            "M001",
            "L001",
        ),
        FakeMember(
            "M002",
            "L002",
        ),
    ]

    options = (
        treatment_options_for_members(
            members
        )
    )

    assert (
        selected_option_index(
            options,
            (
                "member_through",
                (
                    "L999",
                ),
            ),
        )
        == 0
    )
    