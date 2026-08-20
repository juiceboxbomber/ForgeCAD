"""Tests for ForgeCAD member-end fabrication validation."""

from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
    JointTreatmentMode,
)
from forgecad.services.joint_treatment_resolver import (
    CopeInstruction,
    JointTreatmentResolution,
)
from forgecad.services.member_end_validation import (
    MemberEndValidationCode,
    cope_member_end_key,
    validate_member_end_copes,
)


MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.05,
    )


def make_member(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=make_profile(),
        material=MATERIAL,
    )


def make_resolution(
    joint,
    instructions,
):
    treatment = JointTreatment(
        joint=joint,
        mode=JointTreatmentMode.AUTO,
    )

    return JointTreatmentResolution(
        treatment=treatment,
        through_members=(),
        cope_instructions=tuple(
            instructions
        ),
    )


def test_cope_key_identifies_start_end():
    joint_node = Node(
        0,
        0,
        0,
    )

    other_node = Node(
        100,
        0,
        0,
    )

    target_node = Node(
        0,
        100,
        0,
    )

    member = make_member(
        joint_node,
        other_node,
    )

    target = make_member(
        joint_node,
        target_node,
    )

    joint = Joint(
        node=joint_node,
        members=[
            member,
            target,
        ],
    )

    instruction = CopeInstruction(
        joint=joint,
        coped_member=member,
        target_member=target,
    )

    key = cope_member_end_key(
        instruction
    )

    assert key.member is member
    assert key.member_end == "start"


def test_single_cope_is_valid():
    joint_node = Node(
        0,
        0,
        0,
    )

    member = make_member(
        joint_node,
        Node(
            100,
            0,
            0,
        ),
    )

    target = make_member(
        joint_node,
        Node(
            0,
            100,
            0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            member,
            target,
        ],
    )

    instruction = CopeInstruction(
        joint=joint,
        coped_member=member,
        target_member=target,
    )

    resolution = make_resolution(
        joint,
        (
            instruction,
        ),
    )

    validations = (
        validate_member_end_copes(
            (
                resolution,
            )
        )
    )

    assert len(
        validations
    ) == 1

    result = validations[
        0
    ]

    assert (
        result.code
        == MemberEndValidationCode.VALID
    )

    assert result.operation_count == 1
    assert result.is_valid


def test_opposite_member_ends_do_not_conflict():
    start_node = Node(
        0,
        0,
        0,
    )

    end_node = Node(
        100,
        0,
        0,
    )

    member = make_member(
        start_node,
        end_node,
    )

    start_target = make_member(
        start_node,
        Node(
            0,
            100,
            0,
        ),
    )

    end_target = make_member(
        end_node,
        Node(
            100,
            100,
            0,
        ),
    )

    start_joint = Joint(
        node=start_node,
        members=[
            member,
            start_target,
        ],
    )

    end_joint = Joint(
        node=end_node,
        members=[
            member,
            end_target,
        ],
    )

    start_instruction = CopeInstruction(
        joint=start_joint,
        coped_member=member,
        target_member=start_target,
    )

    end_instruction = CopeInstruction(
        joint=end_joint,
        coped_member=member,
        target_member=end_target,
    )

    validations = (
        validate_member_end_copes(
            (
                make_resolution(
                    start_joint,
                    (
                        start_instruction,
                    ),
                ),
                make_resolution(
                    end_joint,
                    (
                        end_instruction,
                    ),
                ),
            )
        )
    )

    assert len(
        validations
    ) == 2

    assert all(
        result.is_valid
        for result in validations
    )


def test_multiple_copes_on_same_end_are_invalid():
    joint_node = Node(
        0,
        0,
        0,
    )

    member = make_member(
        joint_node,
        Node(
            100,
            0,
            0,
        ),
    )

    first_target = make_member(
        joint_node,
        Node(
            0,
            100,
            0,
        ),
    )

    second_target = make_member(
        joint_node,
        Node(
            0,
            0,
            100,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            member,
            first_target,
            second_target,
        ],
    )

    first_instruction = CopeInstruction(
        joint=joint,
        coped_member=member,
        target_member=first_target,
    )

    second_instruction = CopeInstruction(
        joint=joint,
        coped_member=member,
        target_member=second_target,
    )

    resolution = make_resolution(
        joint,
        (
            first_instruction,
            second_instruction,
        ),
    )

    validations = (
        validate_member_end_copes(
            (
                resolution,
            )
        )
    )

    assert len(
        validations
    ) == 1

    result = validations[
        0
    ]

    assert (
        result.code
        == (
            MemberEndValidationCode
            .CONFLICTING_COPES
        )
    )

    assert result.operation_count == 2
    assert not result.is_valid


def test_no_cope_operations_produces_no_end_validations():
    joint_node = Node(
        0,
        0,
        0,
    )

    first = make_member(
        joint_node,
        Node(
            100,
            0,
            0,
        ),
    )

    second = make_member(
        joint_node,
        Node(
            0,
            100,
            0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            first,
            second,
        ],
    )

    resolution = make_resolution(
        joint,
        (),
    )

    validations = (
        validate_member_end_copes(
            (
                resolution,
            )
        )
    )

    assert validations == ()
    