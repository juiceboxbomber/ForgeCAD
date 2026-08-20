"""Tests for ForgeCAD joint detection."""

from forgecad.fabrication import (
    Frame,
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services import (
    connected_members,
    detect_joints,
    frame_connection_nodes,
    member_touches_node,
)


def default_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def default_material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def make_member(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=default_profile(),
        material=default_material(),
    )


def test_joint_starts_empty():
    joint = Joint(
        node=Node(
            0,
            0,
            0,
        )
    )

    assert (
        joint.member_count
        == 0
    )

    assert (
        joint.is_simple
        is False
    )

    assert (
        joint.is_multi_member
        is False
    )


def test_joint_does_not_add_same_member_twice():
    node_a = Node(
        0,
        0,
        0,
    )

    node_b = Node(
        1000,
        0,
        0,
    )

    member = make_member(
        node_a,
        node_b,
    )

    joint = Joint(
        node=node_a
    )

    joint.add_member(
        member
    )

    joint.add_member(
        member
    )

    assert (
        joint.member_count
        == 1
    )


def test_two_members_make_simple_joint():
    center = Node(
        0,
        0,
        0,
    )

    member_1 = make_member(
        center,
        Node(
            1000,
            0,
            0,
        ),
    )

    member_2 = make_member(
        center,
        Node(
            0,
            1000,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            member_1,
            member_2,
        ],
    )

    assert (
        joint.member_count
        == 2
    )

    assert (
        joint.is_simple
        is True
    )

    assert (
        joint.is_multi_member
        is False
    )


def test_three_members_make_multi_member_joint():
    center = Node(
        0,
        0,
        0,
    )

    joint = Joint(
        node=center,
        members=[
            make_member(
                center,
                Node(1000, 0, 0),
            ),
            make_member(
                center,
                Node(0, 1000, 0),
            ),
            make_member(
                center,
                Node(0, 0, 1000),
            ),
        ],
    )

    assert (
        joint.member_count
        == 3
    )

    assert (
        joint.is_multi_member
        is True
    )


def test_member_touches_start_node():
    node_a = Node(
        0,
        0,
        0,
    )

    node_b = Node(
        1000,
        0,
        0,
    )

    member = make_member(
        node_a,
        node_b,
    )

    assert (
        member_touches_node(
            member,
            node_a,
        )
        is True
    )


def test_member_touches_end_node():
    node_a = Node(
        0,
        0,
        0,
    )

    node_b = Node(
        1000,
        0,
        0,
    )

    member = make_member(
        node_a,
        node_b,
    )

    assert (
        member_touches_node(
            member,
            node_b,
        )
        is True
    )


def test_member_does_not_touch_unrelated_node():
    member = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            1000,
            0,
            0,
        ),
    )

    unrelated = Node(
        500,
        500,
        500,
    )

    assert (
        member_touches_node(
            member,
            unrelated,
        )
        is False
    )


def test_connected_members_returns_members_at_node():
    center = Node(
        0,
        0,
        0,
    )

    member_1 = make_member(
        center,
        Node(
            1000,
            0,
            0,
        ),
    )

    member_2 = make_member(
        Node(
            0,
            1000,
            0,
        ),
        center,
    )

    unrelated = make_member(
        Node(
            500,
            500,
            0,
        ),
        Node(
            750,
            500,
            0,
        ),
    )

    frame = Frame(
        members=[
            member_1,
            member_2,
            unrelated,
        ]
    )

    assert connected_members(
        frame,
        center,
    ) == [
        member_1,
        member_2,
    ]


def test_frame_connection_nodes_are_unique():
    node_a = Node(
        0,
        0,
        0,
    )

    node_b = Node(
        1000,
        0,
        0,
    )

    node_c = Node(
        1000,
        1000,
        0,
    )

    frame = Frame(
        members=[
            make_member(
                node_a,
                node_b,
            ),
            make_member(
                node_b,
                node_c,
            ),
        ]
    )

    assert frame_connection_nodes(
        frame
    ) == [
        node_a,
        node_b,
        node_c,
    ]


def test_single_member_has_no_joint():
    frame = Frame(
        members=[
            make_member(
                Node(0, 0, 0),
                Node(1000, 0, 0),
            )
        ]
    )

    assert (
        detect_joints(
            frame
        )
        == []
    )


def test_two_connected_members_detect_one_joint():
    node_a = Node(
        0,
        0,
        0,
    )

    center = Node(
        1000,
        0,
        0,
    )

    node_c = Node(
        1000,
        1000,
        0,
    )

    member_1 = make_member(
        node_a,
        center,
    )

    member_2 = make_member(
        center,
        node_c,
    )

    frame = Frame(
        members=[
            member_1,
            member_2,
        ]
    )

    joints = detect_joints(
        frame
    )

    assert len(
        joints
    ) == 1

    assert (
        joints[0].node
        == center
    )

    assert joints[0].members == [
        member_1,
        member_2,
    ]


def test_three_members_detect_one_three_way_joint():
    center = Node(
        0,
        0,
        0,
    )

    members = [
        make_member(
            center,
            Node(
                1000,
                0,
                0,
            ),
        ),
        make_member(
            center,
            Node(
                0,
                1000,
                0,
            ),
        ),
        make_member(
            center,
            Node(
                0,
                0,
                1000,
            ),
        ),
    ]

    frame = Frame(
        members=members
    )

    joints = detect_joints(
        frame
    )

    assert len(
        joints
    ) == 1

    assert (
        joints[0].member_count
        == 3
    )

    assert (
        joints[0].is_multi_member
        is True
    )


def test_chain_detects_internal_joints_only():
    node_a = Node(
        0,
        0,
        0,
    )

    node_b = Node(
        1000,
        0,
        0,
    )

    node_c = Node(
        2000,
        0,
        0,
    )

    node_d = Node(
        3000,
        0,
        0,
    )

    frame = Frame(
        members=[
            make_member(
                node_a,
                node_b,
            ),
            make_member(
                node_b,
                node_c,
            ),
            make_member(
                node_c,
                node_d,
            ),
        ]
    )

    joints = detect_joints(
        frame
    )

    assert [
        joint.node
        for joint in joints
    ] == [
        node_b,
        node_c,
    ]


def test_equal_coordinate_nodes_are_treated_as_same_connection():
    center_1 = Node(
        1000,
        500,
        250,
    )

    center_2 = Node(
        1000,
        500,
        250,
    )

    member_1 = make_member(
        Node(
            0,
            500,
            250,
        ),
        center_1,
    )

    member_2 = make_member(
        center_2,
        Node(
            2000,
            500,
            250,
        ),
    )

    frame = Frame(
        members=[
            member_1,
            member_2,
        ]
    )

    joints = detect_joints(
        frame
    )

    assert len(
        joints
    ) == 1

    assert (
        joints[0].member_count
        == 2
    )
    