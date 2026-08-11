"""Validate ForgeCAD fabrication operations at member ends."""

from dataclasses import dataclass
from enum import Enum

from forgecad.fabrication import (
    Member,
)
from forgecad.services.joint_extension import (
    member_end_at_joint,
)
from forgecad.services.joint_treatment_resolver import (
    JointTreatmentResolution,
)


class MemberEndValidationCode(
    str,
    Enum,
):
    """Possible validation results for one member end."""

    VALID = "valid"

    CONFLICTING_COPES = "conflicting_copes"


@dataclass(
    frozen=True,
    slots=True,
)
class MemberEndKey:
    """Identify one physical end of one frame member."""

    member: Member

    member_end: str


@dataclass(
    frozen=True,
    slots=True,
)
class MemberEndValidation:
    """Describe fabrication validity for one member end."""

    key: MemberEndKey

    code: MemberEndValidationCode

    operation_count: int

    is_valid: bool


def cope_member_end_key(
    instruction,
) -> MemberEndKey:
    """Return the physical member end affected by a cope."""

    return MemberEndKey(
        member=instruction.coped_member,
        member_end=member_end_at_joint(
            instruction.coped_member,
            instruction.joint,
        ),
    )


def validate_member_end_copes(
    resolutions,
) -> tuple[
    MemberEndValidation,
    ...,
]:
    """
    Validate cope operations assigned to physical member ends.

    A member end may have at most one cylindrical cope operation.
    Multiple cope instructions assigned to the same physical end
    represent conflicting fabrication instructions.
    """

    resolutions = tuple(
        resolutions
    )

    operations_by_end = {}

    for resolution in resolutions:
        if not isinstance(
            resolution,
            JointTreatmentResolution,
        ):
            continue

        for instruction in (
            resolution.cope_instructions
        ):
            key = cope_member_end_key(
                instruction
            )

            operations_by_end.setdefault(
                key,
                [],
            ).append(
                instruction
            )

    validations = []

    for key, operations in (
        operations_by_end.items()
    ):
        operation_count = len(
            operations
        )

        if operation_count > 1:
            code = (
                MemberEndValidationCode
                .CONFLICTING_COPES
            )

            is_valid = False

        else:
            code = (
                MemberEndValidationCode
                .VALID
            )

            is_valid = True

        validations.append(
            MemberEndValidation(
                key=key,
                code=code,
                operation_count=operation_count,
                is_valid=is_valid,
            )
        )

    return tuple(
        validations
    )
