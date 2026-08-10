"""FreeCAD adapter for ForgeCAD joint review status."""

from dataclasses import dataclass

from forgecad.fabrication import (
    Frame,
)
from forgecad.services import (
    detect_joints,
)
from forgecad.services.joint_review_summary import (
    JointReviewSummary,
    summarize_joint_statuses,
)
from forgecad.services.joint_status import (
    JointStatus,
    joint_status_from_saved_treatment,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    frame_member_objects,
    member_from_freecad_object,
)
from forgecad.adapters.freecad.joint_treatment_store import (
    load_joint_treatment,
    node_key,
)


@dataclass(
    frozen=True,
    slots=True,
)
class DocumentJointStatus:
    """Review status for one joint in a FreeCAD document."""

    joint: object

    node_key: str

    status: JointStatus

    @property
    def is_reviewed(
        self,
    ) -> bool:
        """Return True when this joint has been explicitly reviewed."""

        return self.status.is_reviewed

    @property
    def is_manual(
        self,
    ) -> bool:
        """Return True when this joint uses a manual treatment."""

        return self.status.is_manual


@dataclass(
    frozen=True,
    slots=True,
)
class DocumentJointReview:
    """Complete joint-review information for a FreeCAD document."""

    joints: tuple[
        DocumentJointStatus,
        ...,
    ]

    summary: JointReviewSummary


def frame_from_document(
    document,
) -> Frame:
    """Rebuild a domain Frame from generated FreeCAD members."""

    members = [
        member_from_freecad_object(
            obj
        )
        for obj in frame_member_objects(
            document
        )
    ]

    return Frame(
        members=members
    )


def joint_status_for_document_joint(
    document,
    joint,
) -> DocumentJointStatus:
    """Return persistent review status for one detected joint."""

    key = node_key(
        joint.node
    )

    saved_treatment = (
        load_joint_treatment(
            document,
            key,
        )
    )

    status = (
        joint_status_from_saved_treatment(
            saved_treatment
        )
    )

    return DocumentJointStatus(
        joint=joint,
        node_key=key,
        status=status,
    )


def joint_statuses_for_document(
    document,
) -> tuple[
    DocumentJointStatus,
    ...,
]:
    """Return review status for every detected frame joint."""

    if document is None:
        return ()

    frame = frame_from_document(
        document
    )

    joints = detect_joints(
        frame
    )

    return tuple(
        joint_status_for_document_joint(
            document,
            joint,
        )
        for joint in joints
    )


def joint_review_for_document(
    document,
) -> DocumentJointReview:
    """Return complete joint-review information for a document."""

    joint_statuses = (
        joint_statuses_for_document(
            document
        )
    )

    summary = (
        summarize_joint_statuses(
            item.status
            for item in joint_statuses
        )
    )

    return DocumentJointReview(
        joints=joint_statuses,
        summary=summary,
    )
