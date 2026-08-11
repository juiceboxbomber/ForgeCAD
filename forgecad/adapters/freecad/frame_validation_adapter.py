"""FreeCAD adapter for ForgeCAD frame fabrication validation."""

from dataclasses import dataclass

from forgecad.adapters.freecad.joint_status_adapter import (
    frame_from_document,
    joint_statuses_for_document,
)
from forgecad.adapters.freecad.joint_treatment_resolver_adapter import (
    joint_treatment_resolutions_for_document,
)
from forgecad.services import (
    detect_joints,
)
from forgecad.services.frame_validation import (
    FrameValidation,
    validate_frame_joint_statuses,
)
from forgecad.services.member_end_validation import (
    MemberEndValidation,
    validate_member_end_copes,
)


@dataclass(
    frozen=True,
    slots=True,
)
class DocumentFrameValidation:
    """Fabrication validation for one FreeCAD document."""

    validation: FrameValidation

    member_end_validations: tuple[
        MemberEndValidation,
        ...,
    ]

    @property
    def conflicting_member_ends(
        self,
    ) -> tuple[
        MemberEndValidation,
        ...,
    ]:
        """Return invalid member-end fabrication results."""

        return tuple(
            result
            for result
            in self.member_end_validations
            if not result.is_valid
        )

    @property
    def conflict_count(
        self,
    ) -> int:
        """Return the number of conflicting member ends."""

        return len(
            self.conflicting_member_ends
        )

    @property
    def is_ready(
        self,
    ) -> bool:
        """
        Return True when review status and fabrication operations
        are both ready.
        """

        return (
            self.validation.is_ready
            and self.conflict_count == 0
        )

    @property
    def total_joints(
        self,
    ) -> int:
        return self.validation.total_joints

    @property
    def ready_joints(
        self,
    ) -> int:
        return self.validation.ready_joints

    @property
    def not_ready_joints(
        self,
    ) -> int:
        return self.validation.not_ready_joints

    @property
    def invalid_joints(
        self,
    ) -> int:
        return self.validation.invalid_joints


def member_end_validations_for_document(
    document,
) -> tuple[
    MemberEndValidation,
    ...,
]:
    """Validate resolved fabrication operations across the frame."""

    if document is None:
        return ()

    frame = frame_from_document(
        document
    )

    joints = detect_joints(
        frame
    )

    resolutions = (
        joint_treatment_resolutions_for_document(
            document,
            joints,
        )
    )

    return validate_member_end_copes(
        resolutions
    )


def frame_validation_for_document(
    document,
) -> DocumentFrameValidation:
    """Validate fabrication readiness for a FreeCAD document."""

    joint_statuses = (
        joint_statuses_for_document(
            document
        )
    )

    validation = (
        validate_frame_joint_statuses(
            item.status
            for item in joint_statuses
        )
    )

    member_end_validations = (
        member_end_validations_for_document(
            document
        )
    )

    return DocumentFrameValidation(
        validation=validation,
        member_end_validations=member_end_validations,
    )
