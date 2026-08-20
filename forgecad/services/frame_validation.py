"""Frame-level fabrication validation for ForgeCAD."""

from dataclasses import dataclass

from forgecad.services.joint_validation import (
    JointValidation,
    validate_joint_status,
)


@dataclass(
    frozen=True,
    slots=True,
)
class FrameValidation:
    """Summarize fabrication readiness across all joints."""

    joints: tuple[
        JointValidation,
        ...,
    ]

    total_joints: int

    ready_joints: int

    not_ready_joints: int

    invalid_joints: int

    @property
    def is_ready(
        self,
    ) -> bool:
        """Return True when every joint is fabrication-ready."""

        return (
            self.total_joints > 0
            and self.not_ready_joints == 0
            and self.invalid_joints == 0
        )


def validate_frame_joint_statuses(
    statuses,
) -> FrameValidation:
    """Validate fabrication readiness for a collection of joint statuses."""

    validations = tuple(
        validate_joint_status(
            status
        )
        for status in statuses
    )

    total_joints = len(
        validations
    )

    ready_joints = sum(
        1
        for validation in validations
        if validation.is_ready
    )

    invalid_joints = sum(
        1
        for validation in validations
        if not validation.is_valid
    )

    not_ready_joints = (
        total_joints
        - ready_joints
    )

    return FrameValidation(
        joints=validations,
        total_joints=total_joints,
        ready_joints=ready_joints,
        not_ready_joints=not_ready_joints,
        invalid_joints=invalid_joints,
    )
