import pytest

from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)


def test_member_length():
    steel = Material(
        "A513 Type 5 DOM",
        7850.0,
        350.0,
    )

    tube = TubeProfile(
        31.75,
        2.0,
    )

    member = Member(
        start=Node(0.0, 0.0, 0.0),
        end=Node(3000.0, 4000.0, 0.0),
        profile=tube,
        material=steel,
    )

    assert member.length == pytest.approx(5000.0)


def test_member_contains_profile():
    steel = Material("Steel", 7850.0, 350.0)
    tube = TubeProfile(25.4, 2.4)

    member = Member(
        Node(0, 0, 0),
        Node(1000, 0, 0),
        tube,
        steel,
    )

    assert member.profile is tube


def test_member_contains_material():
    steel = Material("Steel", 7850.0, 350.0)
    tube = TubeProfile(25.4, 2.4)

    member = Member(
        Node(0, 0, 0),
        Node(1000, 0, 0),
        tube,
        steel,
    )

    assert member.material is steel
    