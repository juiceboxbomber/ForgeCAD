from forgecad.fabrication import (
    Frame,
    Material,
    Member,
    Node,
    TubeProfile,
)


def test_empty_frame():
    frame = Frame()

    assert frame.node_count == 0
    assert frame.member_count == 0


def test_add_node():
    frame = Frame()

    frame.add_node(Node(0, 0, 0))

    assert frame.node_count == 1


def test_add_member():
    frame = Frame()

    steel = Material("Steel", 7850.0, 350.0)
    tube = TubeProfile(25.4, 2.4)

    a = Node(0, 0, 0)
    b = Node(1000, 0, 0)

    frame.add_node(a)
    frame.add_node(b)

    frame.add_member(
        Member(
            a,
            b,
            tube,
            steel,
        )
    )

    assert frame.member_count == 1
    assert frame.node_count == 2
    