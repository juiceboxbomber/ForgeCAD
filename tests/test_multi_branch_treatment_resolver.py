"""Regression tests for multi-branch member-through treatment resolution."""

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
    resolve_member_through,
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


def test_two_branches_receive_primary_and_secondary_copes():
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

    treatment = JointTreatment.member_through(
        joint,
        through,
    )

    resolution = resolve_member_through(
        treatment
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
