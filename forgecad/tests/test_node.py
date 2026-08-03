from uuid import UUID

from forgecad.fabrication.node import Node


def test_node_creation():
    node = Node.at(100, 200, 300)

    assert isinstance(node.id, UUID)
    assert node.x == 100
    assert node.y == 200
    assert node.z == 300


def test_nodes_have_unique_ids():
    node_a = Node.at(0, 0, 0)
    node_b = Node.at(0, 0, 0)

    assert node_a.id != node_b.id


def test_node_is_immutable():
    node = Node.at(1, 2, 3)

    try:
        node.x = 10
        assert False
    except AttributeError:
        assert True
        