"""Frame-level joint review summaries for ForgeCAD."""

from dataclasses import dataclass

from forgecad.services.joint_status import (
    JointStatus,
)


@dataclass(
    frozen=True,
    slots=True,
)
class JointReviewSummary:
    """Summarize review status across a collection of joints."""

    total_joints: int

    reviewed_joints: int

    unreviewed_joints: int

    manual_treatments: int

    automatic_treatments: int

    invalid_treatments: int

    @property
    def all_reviewed(
        self,
    ) -> bool:
        """Return True when every joint has been reviewed."""

        return (
            self.total_joints > 0
            and self.unreviewed_joints == 0
        )

    @property
    def review_fraction(
        self,
    ) -> float:
        """Return the fraction of joints that have been reviewed."""

        if self.total_joints == 0:
            return 0.0

        return (
            self.reviewed_joints
            / self.total_joints
        )

    @property
    def review_percent(
        self,
    ) -> float:
        """Return review completion as a percentage."""

        return (
            self.review_fraction
            * 100.0
        )


def summarize_joint_statuses(
    statuses,
) -> JointReviewSummary:
    """Build a review summary from JointStatus objects."""

    statuses = tuple(
        statuses
    )

    total_joints = len(
        statuses
    )

    reviewed_joints = sum(
        1
        for status in statuses
        if status.is_reviewed
    )

    unreviewed_joints = (
        total_joints
        - reviewed_joints
    )

    manual_treatments = sum(
        1
        for status in statuses
        if status.is_manual
    )

    automatic_treatments = sum(
        1
        for status in statuses
        if (
            status.is_reviewed
            and not status.is_manual
            and status.code.value
            == "automatic"
        )
    )

    invalid_treatments = sum(
        1
        for status in statuses
        if status.code.value
        == "invalid"
    )

    return JointReviewSummary(
        total_joints=total_joints,
        reviewed_joints=reviewed_joints,
        unreviewed_joints=unreviewed_joints,
        manual_treatments=manual_treatments,
        automatic_treatments=automatic_treatments,
        invalid_treatments=invalid_treatments,
    )
