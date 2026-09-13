"""Tests for Joint Inspector treatment options."""

import math
import sys
import types


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
    is_collinear_through_pair,
    is_right_angle_corner,
    member_display_name,
    member_layout_id,
    option_matches_saved_treatment,
    selected_option_index,
    treatment_options_for_members,
    two_member_angle_degrees,
)


class FakeVector:
    """Minimal FreeCAD-like vector."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class FakeMember:
    """Minimal generated ForgeCAD member."""

    def __init__(
        self,
        member_id,
        layout_id,
        member_name="",
        start=None,
        end=None,
    ):
        self.MemberID = (
            member_id
        )

        self.MemberName = (
            member_name
        )

        self.SourceLayoutID = (
            layout_id
        )

        if start is not None:
            self.StartPoint = (
                start
            )

        if end is not None:
            self.EndPoint = (
                end
            )


def make_90_degree_members():
    """Return two generated members meeting at 90 degrees."""

    center = FakeVector(
        0,
        0,
        0,
    )

    first = FakeMember(
        "M001",
        "L001",
        start=center,
        end=FakeVector(
            500,
            0,
            0,
        ),
    )

    second = FakeMember(
        "M002",
        "L002",
        start=center,
        end=FakeVector(
            0,
            500,
            0,
        ),
    )

    return (
        first,
        second,
    )


def make_60_degree_members():
    """Return two generated members meeting at 60 degrees."""

    center = FakeVector(
        0,
        0,
        0,
    )

    angle = math.radians(
        60.0
    )

    first = FakeMember(
        "M001",
        "L001",
        start=center,
        end=FakeVector(
            500,
            0,
            0,
        ),
    )

    second = FakeMember(
        "M002",
        "L002",
        start=center,
        end=FakeVector(
            500
            * math.cos(
                angle
            ),
            500
            * math.sin(
                angle
            ),
            0,
        ),
    )

    return (
        first,
        second,
    )


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


def test_90_degree_angle_is_detected():
    first, second = (
        make_90_degree_members()
    )

    assert (
        two_member_angle_degrees(
            first,
            second,
        )
        == 90.0
    )

    assert (
        is_right_angle_corner(
            first,
            second,
        )
    )


def test_60_degree_angle_is_not_square_corner():
    first, second = (
        make_60_degree_members()
    )

    angle = (
        two_member_angle_degrees(
            first,
            second,
        )
    )

    assert round(
        angle,
        6,
    ) == 60.0

    assert not (
        is_right_angle_corner(
            first,
            second,
        )
    )


def test_90_degree_corner_has_four_treatment_options():
    first, second = (
        make_90_degree_members()
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

    assert (
        options[
            0
        ].mode
        == JointTreatmentMode.AUTO
    )

    assert (
        options[
            1
        ].mode
        == JointTreatmentMode.MEMBER_THROUGH
    )

    assert (
        options[
            2
        ].mode
        == JointTreatmentMode.MEMBER_THROUGH
    )

    assert (
        options[
            3
        ].mode
        == JointTreatmentMode.BOTH_COPED
    )


def test_90_degree_corner_through_choices_use_layout_ids():
    first, second = (
        make_90_degree_members()
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
        )
    )

    assert (
        options[
            1
        ].through_layout_ids
        == (
            "L001",
        )
    )

    assert (
        options[
            2
        ].through_layout_ids
        == (
            "L002",
        )
    )


def test_90_degree_corner_labels_identify_through_members():
    center = FakeVector(
        0,
        0,
        0,
    )

    first = FakeMember(
        "M001",
        "L001",
        "Rail",
        center,
        FakeVector(
            500,
            0,
            0,
        ),
    )

    second = FakeMember(
        "M002",
        "L002",
        "Crossmember",
        center,
        FakeVector(
            0,
            500,
            0,
        ),
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
        )
    )

    assert (
        options[
            1
        ].label
        == "M001 - Rail Through"
    )

    assert (
        options[
            2
        ].label
        == "M002 - Crossmember Through"
    )

    assert (
        options[
            3
        ].label
        == "Both Mitered"
    )


def test_angled_two_member_corner_has_only_auto_and_miter():
    first, second = (
        make_60_degree_members()
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
    ) == 2

    assert (
        options[
            0
        ].mode
        == JointTreatmentMode.AUTO
    )

    assert (
        options[
            1
        ].mode
        == JointTreatmentMode.BOTH_COPED
    )

    assert (
        options[
            1
        ].label
        == "Both Mitered"
    )


def test_angled_corner_does_not_offer_member_through():
    first, second = (
        make_60_degree_members()
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
        )
    )

    assert all(
        option.mode
        != JointTreatmentMode.MEMBER_THROUGH
        for option
        in options
    )


def test_right_angle_tolerance_allows_88_degree_corner():
    center = FakeVector(
        0,
        0,
        0,
    )

    angle = math.radians(
        88.0
    )

    first = FakeMember(
        "M001",
        "L001",
        start=center,
        end=FakeVector(
            500,
            0,
            0,
        ),
    )

    second = FakeMember(
        "M002",
        "L002",
        start=center,
        end=FakeVector(
            500
            * math.cos(
                angle
            ),
            500
            * math.sin(
                angle
            ),
            0,
        ),
    )

    assert (
        is_right_angle_corner(
            first,
            second,
        )
    )


def test_right_angle_tolerance_rejects_86_degree_corner():
    center = FakeVector(
        0,
        0,
        0,
    )

    angle = math.radians(
        86.0
    )

    first = FakeMember(
        "M001",
        "L001",
        start=center,
        end=FakeVector(
            500,
            0,
            0,
        ),
    )

    second = FakeMember(
        "M002",
        "L002",
        start=center,
        end=FakeVector(
            500
            * math.cos(
                angle
            ),
            500
            * math.sin(
                angle
            ),
            0,
        ),
    )

    assert not (
        is_right_angle_corner(
            first,
            second,
        )
    )


def test_three_member_joint_has_only_geometrically_valid_pair_option():
    center = FakeVector(
        0,
        0,
        0,
    )

    first = FakeMember(
        "M001",
        "L001",
        start=center,
        end=FakeVector(
            -500,
            0,
            0,
        ),
    )

    second = FakeMember(
        "M002",
        "L002",
        start=center,
        end=FakeVector(
            500,
            0,
            0,
        ),
    )

    third = FakeMember(
        "M003",
        "L003",
        start=center,
        end=FakeVector(
            0,
            500,
            0,
        ),
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

    assert len(
        options
    ) == 5

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
    ) == 1

    assert (
        pair_options[
            0
        ].through_layout_ids
        == (
            "L001",
            "L002",
        )
    )


def test_three_member_pair_ids_are_persistent_layout_ids():
    center = FakeVector(
        0,
        0,
        0,
    )

    members = [
        FakeMember(
            "M001",
            "L001",
            start=center,
            end=FakeVector(
                -500,
                0,
                0,
            ),
        ),
        FakeMember(
            "M002",
            "L002",
            start=center,
            end=FakeVector(
                500,
                0,
                0,
            ),
        ),
        FakeMember(
            "M003",
            "L003",
            start=center,
            end=FakeVector(
                0,
                500,
                0,
            ),
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
    }


def test_member_without_layout_id_is_not_manual_choice():
    center = FakeVector(
        0,
        0,
        0,
    )

    first = FakeMember(
        "M001",
        "",
        start=center,
        end=FakeVector(
            500,
            0,
            0,
        ),
    )

    second = FakeMember(
        "M002",
        "L002",
        start=center,
        end=FakeVector(
            0,
            500,
            0,
        ),
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


def test_saved_member_through_matches_90_degree_option():
    first, second = (
        make_90_degree_members()
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
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


def test_saved_miter_matches_legacy_persistence_value():
    first, second = (
        make_60_degree_members()
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
        )
    )

    assert option_matches_saved_treatment(
        options[
            1
        ],
        "both_coped",
        (),
    )

    assert (
        options[
            1
        ].label
        == "Both Mitered"
    )


def test_saved_angled_member_through_falls_back_to_automatic():
    first, second = (
        make_60_degree_members()
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
        )
    )

    index = selected_option_index(
        options,
        (
            "member_through",
            (
                "L001",
            ),
        ),
    )

    assert index == 0

    assert (
        options[
            index
        ].mode
        == JointTreatmentMode.AUTO
    )


def test_saved_90_degree_member_through_selects_correct_option():
    first, second = (
        make_90_degree_members()
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
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
    first, second = (
        make_90_degree_members()
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
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
    first, second = (
        make_90_degree_members()
    )

    options = (
        treatment_options_for_members(
            [
                first,
                second,
            ]
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
    

def test_collinear_opposite_members_are_valid_through_pair():
    center = FakeVector(
        0,
        0,
        0,
    )

    first = FakeMember(
        "M001",
        "L001",
        start=center,
        end=FakeVector(
            -500,
            0,
            0,
        ),
    )

    second = FakeMember(
        "M002",
        "L002",
        start=center,
        end=FakeVector(
            500,
            0,
            0,
        ),
    )

    assert is_collinear_through_pair(
        first,
        second,
    )


def test_non_collinear_members_are_not_valid_through_pair():
    center = FakeVector(
        0,
        0,
        0,
    )

    first = FakeMember(
        "M001",
        "L001",
        start=center,
        end=FakeVector(
            500,
            0,
            0,
        ),
    )

    second = FakeMember(
        "M002",
        "L002",
        start=center,
        end=FakeVector(
            0,
            500,
            0,
        ),
    )

    assert not is_collinear_through_pair(
        first,
        second,
    )


def test_ambiguous_three_direction_joint_has_no_through_pairs():
    center = FakeVector(
        0,
        0,
        0,
    )

    angle = math.radians(
        45.0
    )

    members = [
        FakeMember(
            "M001",
            "L001",
            start=center,
            end=FakeVector(
                500,
                0,
                0,
            ),
        ),
        FakeMember(
            "M002",
            "L002",
            start=center,
            end=FakeVector(
                0,
                500,
                0,
            ),
        ),
        FakeMember(
            "M003",
            "L003",
            start=center,
            end=FakeVector(
                500
                * math.cos(
                    angle
                ),
                500
                * math.sin(
                    angle
                ),
                0,
            ),
        ),
    ]

    options = treatment_options_for_members(
        members
    )

    pair_options = [
        option
        for option in options
        if (
            option.mode
            == JointTreatmentMode.THROUGH_PAIR
        )
    ]

    assert pair_options == []
