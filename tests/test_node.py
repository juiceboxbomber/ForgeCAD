import pytest

from forgecad.fabrication import Node


def test_node_creation():
    node = Node(100.0, 200.0, 300.0)

    assert node.x == 100.0
    assert node.y == 200.0
    assert node.z == 300.0


def test_distance_between_nodes():
    a = Node(0.0, 0.0, 0.0)
    b = Node(3.0, 4.0, 12.0)

    assert a.distance_to(b) == pytest.approx(13.0)


def test_zero_distance():
    node = Node(5.0, 6.0, 7.0)

    assert node.distance_to(node) == 0.0
    