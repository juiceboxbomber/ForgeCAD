"""Regression tests for automatic interior-joint treatment."""

from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
)
from forgecad.services.joint_treatment_resolver import (
    resolve_automatic_treatment,
)


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def make_material():
    return Material(
        name="DOM",
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
        profile=make_profile(),
        material=make_material(),
    )


def test_automatic_two_member_interior_t_uses_continuous_member():
    center = Node(
        500,
        0,
        0,
    )

    through = make_member(
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

    branch = make_member(
        center,
        Node(
            500,
            500,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            through,
            branch,
        ],
    )

    treatment = JointTreatment.automatic(
        joint
    )

    resolution = resolve_automatic_treatment(
        treatment
    )

    assert resolution.through_members == (
        through,
    )

    assert resolution.cope_count == 1

    instruction = (
        resolution.cope_instructions[
            0
        ]
    )

    assert instruction.coped_member is branch
    assert instruction.target_member is through


def test_automatic_three_member_interior_v_uses_continuous_member():
    center = Node(
        500,
        0,
        0,
    )

    through = make_member(
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

    first_branch = make_member(
        center,
        Node(
            250,
            500,
            0,
        ),
    )

    second_branch = make_member(
        center,
        Node(
            750,
            500,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            through,
            first_branch,
            second_branch,
        ],
    )

    treatment = JointTreatment.automatic(
        joint
    )

    resolution = resolve_automatic_treatment(
        treatment
    )

    assert resolution.through_members == (
        through,
    )

    assert resolution.cope_count == 3

    assert (
        resolution.cope_instructions[
            0
        ].coped_member
        is first_branch
    )
    assert (
        resolution.cope_instructions[
            0
        ].target_member
        is through
    )

    assert (
        resolution.cope_instructions[
            1
        ].coped_member
        is second_branch
    )
    assert (
        resolution.cope_instructions[
            1
        ].target_member
        is through
    )

    assert (
        resolution.cope_instructions[
            2
        ].coped_member
        is second_branch
    )
    assert (
        resolution.cope_instructions[
            2
        ].target_member
        is first_branch
    )
    