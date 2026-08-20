"""Tests for ForgeCAD joint member-role analysis."""

from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services import (
    identify_member_roles,
    straightest_member_pair,
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


def test_straightest_pair_returns_none_for_empty_joint():
    joint = Joint(
        node=Node(
            0,
            0,
            0,
        )
    )

    assert (
        straightest_member_pair(
            joint
        )
        is None
    )


def test_straightest_pair_returns_only_pair_for_two_members():
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
        straightest_member_pair(
            joint
        )
        == (
            member_1,
            member_2,
        )
    )


def test_t_joint_identifies_through_pair():
    center = Node(
        0,
        0,
        0,
    )

    left = make_member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
    )

    right = make_member(
        center,
        Node(
            1000,
            0,
            0,
        ),
    )

    branch = make_member(
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
            left,
            branch,
            right,
        ],
    )

    analysis = identify_member_roles(
        joint
    )

    assert analysis.through_members == (
        left,
        right,
    )

    assert analysis.branch_members == (
        branch,
    )

    assert (
        analysis.has_through_pair
        is True
    )

    assert (
        analysis.branch_count
        == 1
    )


def test_straight_two_member_joint_marks_both_as_through():
    center = Node(
        0,
        0,
        0,
    )

    left = make_member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
    )

    right = make_member(
        center,
        Node(
            1000,
            0,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            left,
            right,
        ],
    )

    analysis = identify_member_roles(
        joint
    )

    assert analysis.through_members == (
        left,
        right,
    )

    assert analysis.branch_members == ()


def test_corner_joint_has_no_through_pair():
    center = Node(
        0,
        0,
        0,
    )

    member_x = make_member(
        center,
        Node(
            1000,
            0,
            0,
        ),
    )

    member_y = make_member(
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
            member_x,
            member_y,
        ],
    )

    analysis = identify_member_roles(
        joint
    )

    assert (
        analysis.through_members
        == ()
    )

    assert analysis.branch_members == (
        member_x,
        member_y,
    )


def test_three_way_non_t_joint_has_no_through_pair():
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

    joint = Joint(
        node=center,
        members=members,
    )

    analysis = identify_member_roles(
        joint
    )

    assert (
        analysis.through_members
        == ()
    )

    assert (
        analysis.branch_members
        == tuple(members)
    )


def test_four_member_joint_identifies_straightest_pair():
    center = Node(
        0,
        0,
        0,
    )

    left = make_member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
    )

    right = make_member(
        center,
        Node(
            1000,
            0,
            0,
        ),
    )

    up = make_member(
        center,
        Node(
            0,
            1000,
            0,
        ),
    )

    forward = make_member(
        center,
        Node(
            0,
            0,
            1000,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            left,
            up,
            right,
            forward,
        ],
    )

    analysis = identify_member_roles(
        joint
    )

    assert analysis.through_members == (
        left,
        right,
    )

    assert analysis.branch_members == (
        up,
        forward,
    )


def test_nearly_straight_pair_within_tolerance_is_through():
    center = Node(
        0,
        0,
        0,
    )

    left = make_member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
    )

    almost_right = make_member(
        center,
        Node(
            1000,
            35,
            0,
        ),
    )

    branch = make_member(
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
            left,
            almost_right,
            branch,
        ],
    )

    analysis = identify_member_roles(
        joint,
        straight_tolerance_degrees=3.0,
    )

    assert analysis.through_members == (
        left,
        almost_right,
    )

    assert analysis.branch_members == (
        branch,
    )


def test_pair_outside_tolerance_is_not_through():
    center = Node(
        0,
        0,
        0,
    )

    left = make_member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
    )

    angled = make_member(
        center,
        Node(
            1000,
            100,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            left,
            angled,
        ],
    )

    analysis = identify_member_roles(
        joint,
        straight_tolerance_degrees=3.0,
    )

    assert (
        analysis.through_members
        == ()
    )

    assert analysis.branch_members == (
        left,
        angled,
    )


def test_single_member_is_branch_only():
    center = Node(
        0,
        0,
        0,
    )

    member = make_member(
        center,
        Node(
            1000,
            0,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            member,
        ],
    )

    analysis = identify_member_roles(
        joint
    )

    assert (
        analysis.through_members
        == ()
    )

    assert analysis.branch_members == (
        member,
    )
    