"""Tests for ForgeCAD joint treatment definitions."""

import pytest

from forgecad.fabrication.joint import (
    Joint,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
    JointTreatmentMode,
)
from forgecad.fabrication.material import (
    Material,
)
from forgecad.fabrication.member import (
    Member,
)
from forgecad.fabrication.node import (
    Node,
)
from forgecad.fabrication.tube_profile import (
    TubeProfile,
)


PROFILE = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)


MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


def make_member(
    start,
    end,
):
    """Create one test tube member."""

    return Member(
        start=start,
        end=end,
        profile=PROFILE,
        material=MATERIAL,
    )


def make_corner():
    """Return a simple two-member corner joint."""

    center = Node(
        0,
        0,
        0,
    )

    horizontal = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    vertical = make_member(
        center,
        Node(
            0,
            500,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            horizontal,
            vertical,
        ],
    )

    return (
        joint,
        horizontal,
        vertical,
    )


def make_t_joint():
    """Return a standard three-member T-joint."""

    center = Node(
        0,
        0,
        0,
    )

    left = make_member(
        center,
        Node(
            -500,
            0,
            0,
        ),
    )

    right = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    branch = make_member(
        center,
        Node(
            0,
            500,
            0,
        ),
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


def test_default_treatment_is_auto():
    joint, first, second = (
        make_corner()
    )

    treatment = JointTreatment(
        joint=joint
    )

    assert (
        treatment.mode
        == JointTreatmentMode.AUTO
    )

    assert treatment.is_automatic

    assert (
        treatment.through_members
        == ()
    )

    assert (
        treatment.coped_members
        == ()
    )


def test_automatic_factory():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.automatic(
            joint
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.AUTO
    )


def test_corner_first_member_can_continue_through():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            first,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.MEMBER_THROUGH
    )

    assert treatment.through_members == (
        first,
    )

    assert treatment.coped_members == (
        second,
    )

    assert (
        treatment.through_member_count
        == 1
    )

    assert (
        treatment.cope_member_count
        == 1
    )


def test_corner_second_member_can_continue_through():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            second,
        )
    )

    assert treatment.through_members == (
        second,
    )

    assert treatment.coped_members == (
        first,
    )


def test_corner_can_cope_both_members():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.both_coped(
            joint
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.BOTH_COPED
    )

    assert treatment.coped_members == (
        first,
        second,
    )

    assert (
        treatment.cope_member_count
        == 2
    )

    assert (
        treatment.through_member_count
        == 0
    )


def test_t_joint_can_select_through_pair():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    treatment = (
        JointTreatment.through_pair(
            joint,
            left,
            right,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.THROUGH_PAIR
    )

    assert treatment.through_members == (
        left,
        right,
    )

    assert treatment.coped_members == (
        branch,
    )


def test_t_joint_can_choose_different_through_pair():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    treatment = (
        JointTreatment.through_pair(
            joint,
            left,
            branch,
        )
    )

    assert treatment.through_members == (
        left,
        branch,
    )

    assert treatment.coped_members == (
        right,
    )


def test_auto_rejects_explicit_through_member():
    joint, first, second = (
        make_corner()
    )

    with pytest.raises(
        ValueError
    ):
        JointTreatment(
            joint=joint,
            mode=(
                JointTreatmentMode.AUTO
            ),
            through_members=(
                first,
            ),
        )


def test_member_through_requires_one_member():
    joint, first, second = (
        make_corner()
    )

    with pytest.raises(
        ValueError
    ):
        JointTreatment(
            joint=joint,
            mode=(
                JointTreatmentMode.MEMBER_THROUGH
            ),
        )


def test_member_through_rejects_two_members():
    joint, first, second = (
        make_corner()
    )

    with pytest.raises(
        ValueError
    ):
        JointTreatment(
            joint=joint,
            mode=(
                JointTreatmentMode.MEMBER_THROUGH
            ),
            through_members=(
                first,
                second,
            ),
        )


def test_both_coped_rejects_three_member_joint():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    with pytest.raises(
        ValueError
    ):
        JointTreatment.both_coped(
            joint
        )


def test_through_pair_requires_two_members():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    with pytest.raises(
        ValueError
    ):
        JointTreatment(
            joint=joint,
            mode=(
                JointTreatmentMode.THROUGH_PAIR
            ),
            through_members=(
                left,
            ),
        )


def test_treatment_rejects_member_not_in_joint():
    joint, first, second = (
        make_corner()
    )

    unrelated = make_member(
        Node(
            1000,
            1000,
            0,
        ),
        Node(
            1500,
            1000,
            0,
        ),
    )

    with pytest.raises(
        ValueError
    ):
        JointTreatment.member_through(
            joint,
            unrelated,
        )


def test_through_pair_rejects_duplicate_member():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    with pytest.raises(
        ValueError
    ):
        JointTreatment.through_pair(
            joint,
            left,
            left,
        )
        