"""Regression tests for topology-aware Joint Inspector treatment options."""

from types import SimpleNamespace

from forgecad.adapters.freecad.joint_treatment_options import (
    treatment_options_for_members,
)


def point(x, y, z=0.0):
    return SimpleNamespace(
        x=float(x),
        y=float(y),
        z=float(z),
    )


def member(member_id, layout_id, start, end):
    return SimpleNamespace(
        MemberID=member_id,
        MemberName="",
        SourceLayoutID=layout_id,
        StartPoint=start,
        EndPoint=end,
    )


def test_three_member_branch_joint_only_offers_natural_through_member():
    through = member(
        "M001",
        "layout-through",
        point(-500, 0),
        point(500, 0),
    )
    first_branch = member(
        "M002",
        "layout-branch-1",
        point(0, 0),
        point(-250, 400),
    )
    second_branch = member(
        "M003",
        "layout-branch-2",
        point(0, 0),
        point(250, 400),
    )

    options = treatment_options_for_members(
        [through, first_branch, second_branch]
    )

    assert [option.label for option in options] == [
        "Automatic",
        "M001 Through",
    ]


def test_ambiguous_three_member_joint_keeps_complete_fallback_options():
    first = member(
        "M001",
        "layout-1",
        point(0, 0),
        point(500, 0),
    )
    second = member(
        "M002",
        "layout-2",
        point(0, 0),
        point(0, 500),
    )
    third = member(
        "M003",
        "layout-3",
        point(0, 0),
        point(-300, 400),
    )

    options = treatment_options_for_members(
        [first, second, third]
    )

    assert [option.label for option in options] == [
        "Automatic",
        "M001 Through",
        "M002 Through",
        "M003 Through",
        "M001 + M002 Through Pair",
        "M001 + M003 Through Pair",
        "M002 + M003 Through Pair",
    ]
