"""Tests for ForgeCAD tube notch analysis."""

import pytest

from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services import (
    BRANCH_END_END,
    BRANCH_END_START,
    branch_through_angle,
    build_notch_specification,
    member_end_at_node,
    notch_specifications_for_joint,
    through_outside_diameter,
)


def material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def profile(
    outside_diameter=44.45,
    wall_thickness=3.048,
):
    return TubeProfile(
        outside_diameter=outside_diameter,
        wall_thickness=wall_thickness,
    )


def member(
    start,
    end,
    tube_profile=None,
):
    return Member(
        start=start,
        end=end,
        profile=(
            tube_profile
            or profile()
        ),
        material=material(),
    )


def make_t_joint(
    branch_profile=None,
    through_profile=None,
):
    center = Node(
        0,
        0,
        0,
    )

    through_profile = (
        through_profile
        or profile()
    )

    left = member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
        through_profile,
    )

    right = member(
        center,
        Node(
            1000,
            0,
            0,
        ),
        through_profile,
    )

    branch = member(
        center,
        Node(
            0,
            1000,
            0,
        ),
        branch_profile
        or profile(),
    )

    joint = Joint(
        node=center,
        members=[
            left,
            right,
            branch,
        ],
    )

    return (
        joint,
        left,
        right,
        branch,
    )


def test_member_end_at_node_detects_start():
    start = Node(
        0,
        0,
        0,
    )

    tube = member(
        start,
        Node(
            1000,
            0,
            0,
        ),
    )

    assert (
        member_end_at_node(
            tube,
            start,
        )
        == BRANCH_END_START
    )


def test_member_end_at_node_detects_end():
    end = Node(
        0,
        0,
        0,
    )

    tube = member(
        Node(
            1000,
            0,
            0,
        ),
        end,
    )

    assert (
        member_end_at_node(
            tube,
            end,
        )
        == BRANCH_END_END
    )


def test_member_end_at_node_rejects_unrelated_node():
    tube = member(
        Node(0, 0, 0),
        Node(1000, 0, 0),
    )

    with pytest.raises(
        ValueError
    ):
        member_end_at_node(
            tube,
            Node(
                500,
                500,
                500,
            ),
        )


def test_through_diameter_returns_common_diameter():
    joint, left, right, branch = (
        make_t_joint()
    )

    assert through_outside_diameter(
        (
            left,
            right,
        )
    ) == pytest.approx(
        44.45
    )


def test_through_diameter_requires_two_members():
    joint, left, right, branch = (
        make_t_joint()
    )

    with pytest.raises(
        ValueError
    ):
        through_outside_diameter(
            (left,)
        )


def test_through_diameter_rejects_mismatched_profiles():
    center = Node(
        0,
        0,
        0,
    )

    left = member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
        profile(
            outside_diameter=44.45
        ),
    )

    right = member(
        center,
        Node(
            1000,
            0,
            0,
        ),
        profile(
            outside_diameter=31.75,
            wall_thickness=2.413,
        ),
    )

    with pytest.raises(
        ValueError
    ):
        through_outside_diameter(
            (
                left,
                right,
            )
        )


def test_90_degree_branch_reports_90_degrees():
    joint, left, right, branch = (
        make_t_joint()
    )

    assert branch_through_angle(
        branch,
        left,
        joint.node,
    ) == pytest.approx(
        90.0
    )


def test_oblique_branch_reports_acute_axis_angle():
    center = Node(
        0,
        0,
        0,
    )

    through = member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
    )

    branch = member(
        center,
        Node(
            500,
            866.0254038,
            0,
        ),
    )

    assert branch_through_angle(
        branch,
        through,
        center,
    ) == pytest.approx(
        60.0,
        abs=0.001,
    )


def test_notch_spec_contains_branch_profile_data():
    branch_profile = profile(
        outside_diameter=31.75,
        wall_thickness=2.413,
    )

    joint, left, right, branch = (
        make_t_joint(
            branch_profile=branch_profile,
        )
    )

    specification = (
        build_notch_specification(
            joint,
            branch,
            (
                left,
                right,
            ),
        )
    )

    assert (
        specification.branch_outside_diameter
        == pytest.approx(
            31.75
        )
    )

    assert (
        specification.branch_inside_diameter
        == pytest.approx(
            31.75
            - 2 * 2.413
        )
    )

    assert (
        specification.branch_wall_thickness
        == pytest.approx(
            2.413
        )
    )


def test_notch_spec_contains_through_diameter():
    joint, left, right, branch = (
        make_t_joint()
    )

    specification = (
        build_notch_specification(
            joint,
            branch,
            (
                left,
                right,
            ),
        )
    )

    assert (
        specification.through_outside_diameter
        == pytest.approx(
            44.45
        )
    )


def test_notch_spec_records_branch_start_end():
    joint, left, right, branch = (
        make_t_joint()
    )

    specification = (
        build_notch_specification(
            joint,
            branch,
            (
                left,
                right,
            ),
        )
    )

    assert (
        specification.branch_end
        == BRANCH_END_START
    )


def test_reversed_branch_records_end():
    center = Node(
        0,
        0,
        0,
    )

    left = member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
    )

    right = member(
        center,
        Node(
            1000,
            0,
            0,
        ),
    )

    branch = member(
        Node(
            0,
            1000,
            0,
        ),
        center,
    )

    joint = Joint(
        node=center,
        members=[
            left,
            right,
            branch,
        ],
    )

    specification = (
        build_notch_specification(
            joint,
            branch,
            (
                left,
                right,
            ),
        )
    )

    assert (
        specification.branch_end
        == BRANCH_END_END
    )


def test_t_joint_produces_one_notch_specification():
    joint, left, right, branch = (
        make_t_joint()
    )

    specifications = (
        notch_specifications_for_joint(
            joint
        )
    )

    assert len(
        specifications
    ) == 1

    assert (
        specifications[0].branch_member
        is branch
    )


def test_corner_joint_produces_no_notch_specifications():
    center = Node(
        0,
        0,
        0,
    )

    joint = Joint(
        node=center,
        members=[
            member(
                center,
                Node(
                    1000,
                    0,
                    0,
                ),
            ),
            member(
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
        notch_specifications_for_joint(
            joint
        )
        == ()
    )


def test_multi_branch_joint_produces_one_spec_per_branch():
    center = Node(
        0,
        0,
        0,
    )

    left = member(
        center,
        Node(
            -1000,
            0,
            0,
        ),
    )

    right = member(
        center,
        Node(
            1000,
            0,
            0,
        ),
    )

    branch_y = member(
        center,
        Node(
            0,
            1000,
            0,
        ),
    )

    branch_z = member(
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
            branch_y,
            right,
            branch_z,
        ],
    )

    specifications = (
        notch_specifications_for_joint(
            joint
        )
    )

    assert len(
        specifications
    ) == 2

    assert {
        spec.branch_member
        for spec in specifications
    } == {
        branch_y,
        branch_z,
    }
    