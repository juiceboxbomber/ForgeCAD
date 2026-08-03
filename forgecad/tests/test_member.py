import pytest

from forgecad.fabrication.material import Material
from forgecad.fabrication.member import Member
from forgecad.fabrication.node import Node
from forgecad.fabrication.tube_profile import TubeProfile


@pytest.fixture
def tube_profile():
    return TubeProfile(
        outside_diameter_mm=44.45,
        wall_thickness_mm=3.048,
    )


@pytest.fixture
def steel():
    return Material(
        name="4130 Chromoly",
        density=7.85e-6,
        yield_strength=435,
        ultimate_strength=670,
        elastic_modulus=205000,
    )


def test_member_creation(tube_profile, steel):
    start = Node.at(0, 0, 0)
    end = Node.at(100, 0, 0)

    member = Member(
        start_node=start,
        end_node=end,
        profile=tube_profile,
        material=steel,
    )

    assert member.start_node == start
    assert member.end_node == end


def test_member_length(tube_profile, steel):
    start = Node.at(0, 0, 0)
    end = Node.at(300, 400, 0)

    member = Member(
        start_node=start,
        end_node=end,
        profile=tube_profile,
        material=steel,
    )

    assert member.length == pytest.approx(500)
    