"""Tests for ForgeCAD joint treatment resolution."""

from forgecad.fabrication.joint import (
    Joint,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
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
from forgecad.services.joint_treatment_resolver import (
    resolve_joint_treatment,
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
    return Member(
        start=start,
        end=end,
        profile=PROFILE,
        material=MATERIAL,
    )


def make_corner():
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


def test_auto_t_joint_resolves_branch_cope():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    treatment = (
        JointTreatment.automatic(
            joint
        )
    )

    resolution = (
        resolve_joint_treatment(
            treatment
        )
    )

    assert resolution.through_members == (
        left,
        right,
    )

    assert (
        resolution.cope_count
        == 1
    )

    instruction = (
        resolution.cope_instructions[
            0
        ]
    )

    assert (
        instruction.coped_member
        is branch
    )

    assert (
        instruction.target_member
        is left
    )


def test_auto_corner_produces_no_cope():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.automatic(
            joint
        )
    )

    resolution = (
        resolve_joint_treatment(
            treatment
        )
    )

    assert (
        resolution.through_members
        == ()
    )

    assert (
        resolution.cope_instructions
        == ()
    )


def test_corner_first_member_through():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            first,
        )
    )

    resolution = (
        resolve_joint_treatment(
            treatment
        )
    )

    assert resolution.through_members == (
        first,
    )

    assert (
        resolution.cope_count
        == 1
    )

    instruction = (
        resolution.cope_instructions[
            0
        ]
    )

    assert (
        instruction.coped_member
        is second
    )

    assert (
        instruction.target_member
        is first
    )


def test_corner_second_member_through():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            second,
        )
    )

    resolution = (
        resolve_joint_treatment(
            treatment
        )
    )

    instruction = (
        resolution.cope_instructions[
            0
        ]
    )

    assert (
        instruction.coped_member
        is first
    )

    assert (
        instruction.target_member
        is second
    )


def test_corner_both_coped_produces_two_instructions():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.both_coped(
            joint
        )
    )

    resolution = (
        resolve_joint_treatment(
            treatment
        )
    )

    assert (
        resolution.cope_count
        == 2
    )

    first_instruction = (
        resolution.cope_instructions[
            0
        ]
    )

    second_instruction = (
        resolution.cope_instructions[
            1
        ]
    )

    assert (
        first_instruction.coped_member
        is first
    )

    assert (
        first_instruction.target_member
        is second
    )

    assert (
        second_instruction.coped_member
        is second
    )

    assert (
        second_instruction.target_member
        is first
    )


def test_t_joint_explicit_through_pair():
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

    resolution = (
        resolve_joint_treatment(
            treatment
        )
    )

    assert resolution.through_members == (
        left,
        right,
    )

    assert (
        resolution.cope_count
        == 1
    )

    instruction = (
        resolution.cope_instructions[
            0
        ]
    )

    assert (
        instruction.coped_member
        is branch
    )

    assert (
        instruction.target_member
        is left
    )


def test_t_joint_can_choose_nonstandard_through_pair():
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

    resolution = (
        resolve_joint_treatment(
            treatment
        )
    )

    assert resolution.through_members == (
        left,
        branch,
    )

    assert (
        resolution.cope_count
        == 1
    )

    instruction = (
        resolution.cope_instructions[
            0
        ]
    )

    assert (
        instruction.coped_member
        is right
    )

    assert (
        instruction.target_member
        is left
    )


def test_multi_branch_explicit_pair_copes_all_remaining_members():
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

    up = make_member(
        center,
        Node(
            0,
            500,
            0,
        ),
    )

    forward = make_member(
        center,
        Node(
            0,
            0,
            500,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            left,
            right,
            up,
            forward,
        ],
    )

    treatment = (
        JointTreatment.through_pair(
            joint,
            left,
            right,
        )
    )

    resolution = (
        resolve_joint_treatment(
            treatment
        )
    )

    assert (
        resolution.cope_count
        == 2
    )

    assert {
        instruction.coped_member
        for instruction
        in resolution.cope_instructions
    } == {
        up,
        forward,
    }


def test_resolution_keeps_original_treatment():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            first,
        )
    )

    resolution = (
        resolve_joint_treatment(
            treatment
        )
    )

    assert (
        resolution.treatment
        is treatment
    )
    