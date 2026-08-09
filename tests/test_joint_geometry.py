"""Tests for ForgeCAD joint geometry analysis."""

import pytest

from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services import (
    JOINT_CORNER,
    JOINT_INVALID,
    JOINT_MULTI_MEMBER,
    JOINT_STRAIGHT,
    JOINT_T,
    analyze_joint,
    angle_between_members,
    classify_joint,
    is_straight_angle,
    joint_angles,
    member_direction_from_node,
    member_other_node,
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


def test_member_other_node_when_joint_is_start():
    joint_node = Node(
        0,
        0,
        0,
    )

    other_node = Node(
        1000,
        0,
        0,
    )

    member = make_member(
        joint_node,
        other_node,
    )

    assert (
        member_other_node(
            member,
            joint_node,
        )
        == other_node
    )


def test_member_other_node_when_joint_is_end():
    other_node = Node(
        1000,
        0,
        0,
    )

    joint_node = Node(
        0,
        0,
        0,
    )

    member = make_member(
        other_node,
        joint_node,
    )

    assert (
        member_other_node(
            member,
            joint_node,
        )
        == other_node
    )


def test_member_other_node_rejects_unrelated_node():
    member = make_member(
        Node(0, 0, 0),
        Node(1000, 0, 0),
    )

    with pytest.raises(
        ValueError
    ):
        member_other_node(
            member,
            Node(
                500,
                500,
                500,
            ),
        )


def test_member_direction_is_unit_vector():
    joint_node = Node(
        0,
        0,
        0,
    )

    member = make_member(
        joint_node,
        Node(
            1000,
            0,
            0,
        ),
    )

    direction = (
        member_direction_from_node(
            member,
            joint_node,
        )
    )

    assert direction == pytest.approx(
        (
            1.0,
            0.0,
            0.0,
        )
    )


def test_member_direction_handles_member_reversal():
    joint_node = Node(
        0,
        0,
        0,
    )

    member = make_member(
        Node(
            0,
            1000,
            0,
        ),
        joint_node,
    )

    direction = (
        member_direction_from_node(
            member,
            joint_node,
        )
    )

    assert direction == pytest.approx(
        (
            0.0,
            1.0,
            0.0,
        )
    )


def test_perpendicular_members_have_90_degree_angle():
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

    assert angle_between_members(
        member_x,
        member_y,
        center,
    ) == pytest.approx(
        90.0
    )


def test_opposite_members_have_180_degree_angle():
    center = Node(
        0,
        0,
        0,
    )

    member_right = make_member(
        center,
        Node(
            1000,
            0,
            0,
        ),
    )

    member_left = make_member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
    )

    assert angle_between_members(
        member_right,
        member_left,
        center,
    ) == pytest.approx(
        180.0
    )


def test_same_direction_members_have_zero_degree_angle():
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
            500,
            0,
            0,
        ),
    )

    assert angle_between_members(
        member_1,
        member_2,
        center,
    ) == pytest.approx(
        0.0
    )


def test_joint_angles_returns_unique_member_pairs():
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
        ],
    )

    angles = joint_angles(
        joint
    )

    assert len(
        angles
    ) == 3

    assert all(
        angle.angle_degrees
        == pytest.approx(
            90.0
        )
        for angle in angles
    )


def test_straight_angle_accepts_180_degrees():
    assert (
        is_straight_angle(
            180.0
        )
        is True
    )


def test_straight_angle_accepts_value_inside_tolerance():
    assert (
        is_straight_angle(
            178.0,
            tolerance_degrees=3.0,
        )
        is True
    )


def test_straight_angle_rejects_value_outside_tolerance():
    assert (
        is_straight_angle(
            175.0,
            tolerance_degrees=3.0,
        )
        is False
    )


def test_two_opposite_members_classify_as_straight():
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
                Node(
                    1000,
                    0,
                    0,
                ),
            ),
            make_member(
                center,
                Node(
                    -1000,
                    0,
                    0,
                ),
            ),
        ],
    )

    assert (
        classify_joint(
            joint
        )
        == JOINT_STRAIGHT
    )


def test_two_perpendicular_members_classify_as_corner():
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
        ],
    )

    assert (
        classify_joint(
            joint
        )
        == JOINT_CORNER
    )


def test_three_members_with_straight_pair_classify_as_t_joint():
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
                Node(
                    1000,
                    0,
                    0,
                ),
            ),
            make_member(
                center,
                Node(
                    -1000,
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
        ],
    )

    assert (
        classify_joint(
            joint
        )
        == JOINT_T
    )


def test_three_members_without_straight_pair_classify_as_multi_member():
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
        ],
    )

    assert (
        classify_joint(
            joint
        )
        == JOINT_MULTI_MEMBER
    )


def test_four_member_joint_classifies_as_multi_member():
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
                Node(-1000, 0, 0),
            ),
            make_member(
                center,
                Node(0, 1000, 0),
            ),
            make_member(
                center,
                Node(0, -1000, 0),
            ),
        ],
    )

    assert (
        classify_joint(
            joint
        )
        == JOINT_MULTI_MEMBER
    )


def test_empty_joint_classifies_as_invalid():
    joint = Joint(
        node=Node(
            0,
            0,
            0,
        )
    )

    assert (
        classify_joint(
            joint
        )
        == JOINT_INVALID
    )


def test_analysis_contains_classification_and_angles():
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
        ],
    )

    analysis = analyze_joint(
        joint
    )

    assert (
        analysis.joint
        is joint
    )

    assert (
        analysis.classification
        == JOINT_CORNER
    )

    assert len(
        analysis.angles
    ) == 1

    assert (
        analysis.angles[0].angle_degrees
        == pytest.approx(
            90.0
        )
    )
    