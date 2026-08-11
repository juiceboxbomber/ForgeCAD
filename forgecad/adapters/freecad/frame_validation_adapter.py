"""FreeCAD adapter for ForgeCAD frame fabrication validation."""

from dataclasses import dataclass

from forgecad.adapters.freecad.joint_status_adapter import (
    joint_statuses_for_document,
)
from forgecad.services.frame_validation import (
    FrameValidation,
    validate_frame_joint_statuses,
)


@dataclass(
    frozen=True,
    slots=True,
)
class DocumentFrameValidation:
    """Fabrication validation for one FreeCAD document."""

    validation: FrameValidation

    @property
    def is_ready(
        self,
    ) -> bool:
        """Return True when the document frame is fabrication-ready."""

        return self.validation.is_ready

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

    return DocumentFrameValidation(
        validation=validation
    )
