import pytest

from forgecad.fabrication.frame import Frame
from forgecad.fabrication.material import Material
from forgecad.fabrication.member import Member
from forgecad.fabrication.node import Node
from forgecad.fabrication.tube_profile import TubeProfile


@pytest.fixture
def tube():
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


def test_frame_creation():
    frame = Frame("Test Chassis")

    assert frame.name == "Test Chassis"
    assert len(frame.nodes) == 0
    assert len(frame.members) == 0


def test_add_member_adds_nodes(tube, steel):
    node_a = Node.at(0, 0, 0)
    node_b = Node.at(1000, 0, 0)

    member = Member(
        node_a,
        node_b,
        tube,
        steel,
    )

    frame = Frame("Test Frame")

    frame.add_member(member)

    assert len(frame.members) == 1
    assert len(frame.nodes) == 2


def test_total_length(tube, steel):
    node_a = Node.at(0, 0, 0)
    node_b = Node.at(300, 400, 0)

    member = Member(
        node_a,
        node_b,
        tube,
        steel,
    )

    frame = Frame("Test Frame")
    frame.add_member(member)

    assert frame.total_length == pytest.approx(500)
    