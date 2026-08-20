"""Fabrication validation for ForgeCAD joints."""

from dataclasses import dataclass
from enum import Enum

from forgecad.services.joint_status import (
    JointStatus,
    JointStatusCode,
)


class JointValidationCode(
    str,
    Enum,
):
    """Possible fabrication-validation results for a joint."""

    READY = "ready"

    UNREVIEWED = "unreviewed"

    INVALID_TREATMENT = "invalid_treatment"


@dataclass(
    frozen=True,
    slots=True,
)
class JointValidation:
    """Describe whether one joint is ready for fabrication."""

    code: JointValidationCode

    message: str

    is_valid: bool

    is_ready: bool


READY_VALIDATION = JointValidation(
    code=JointValidationCode.READY,
    message="Joint is ready for fabrication.",
    is_valid=True,
    is_ready=True,
)

UNREVIEWED_VALIDATION = JointValidation(
    code=JointValidationCode.UNREVIEWED,
    message="Joint has not been reviewed.",
    is_valid=True,
    is_ready=False,
)

INVALID_TREATMENT_VALIDATION = JointValidation(
    code=JointValidationCode.INVALID_TREATMENT,
    message="Joint treatment is invalid.",
    is_valid=False,
    is_ready=False,
)


def validate_joint_status(
    status: JointStatus,
) -> JointValidation:
    """
    Validate fabrication readiness from a joint's review status.

    This is intentionally the first validation layer. More
    geometric and fabrication rules can be added without
    coupling validation to FreeCAD.
    """

    if (
        status.code
        == JointStatusCode.INVALID
    ):
        return (
            INVALID_TREATMENT_VALIDATION
        )

    if not status.is_reviewed:
        return (
            UNREVIEWED_VALIDATION
        )

    return READY_VALIDATION
