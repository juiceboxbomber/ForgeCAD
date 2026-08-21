"""Joint review-status helpers for ForgeCAD."""

from dataclasses import dataclass
from enum import Enum


class JointStatusCode(
    str,
    Enum,
):
    """Persistent/display states for a ForgeCAD joint."""

    UNREVIEWED = (
        "unreviewed"
    )

    AUTOMATIC = (
        "automatic"
    )

    NEEDS_DECISION = (
        "needs_decision"
    )

    MEMBER_THROUGH = (
        "member_through"
    )

    BOTH_MITERED = (
        "both_mitered"
    )

    THROUGH_PAIR = (
        "through_pair"
    )

    INVALID = (
        "invalid"
    )


@dataclass(
    frozen=True,
    slots=True,
)
class JointStatus:
    """Describe the review and treatment state of one joint."""

    code: JointStatusCode

    label: str

    is_reviewed: bool

    is_manual: bool

    @property
    def needs_attention(
        self,
    ) -> bool:
        """
        Return True when the joint requires designer attention.

        Unreviewed and decision-required joints require attention.

        Invalid saved treatments also require attention even
        though a treatment record exists.
        """

        return (
            not self.is_reviewed
            or self.code
            in (
                JointStatusCode.NEEDS_DECISION,
                JointStatusCode.INVALID,
            )
        )


UNREVIEWED_STATUS = JointStatus(
    code=JointStatusCode.UNREVIEWED,
    label="Unreviewed",
    is_reviewed=False,
    is_manual=False,
)

AUTOMATIC_STATUS = JointStatus(
    code=JointStatusCode.AUTOMATIC,
    label="Automatic",
    is_reviewed=True,
    is_manual=False,
)

NEEDS_DECISION_STATUS = JointStatus(
    code=JointStatusCode.NEEDS_DECISION,
    label="Needs Decision",
    is_reviewed=False,
    is_manual=False,
)

MEMBER_THROUGH_STATUS = JointStatus(
    code=JointStatusCode.MEMBER_THROUGH,
    label="Member Through",
    is_reviewed=True,
    is_manual=True,
)

BOTH_MITERED_STATUS = JointStatus(
    code=JointStatusCode.BOTH_MITERED,
    label="Both Mitered",
    is_reviewed=True,
    is_manual=True,
)

THROUGH_PAIR_STATUS = JointStatus(
    code=JointStatusCode.THROUGH_PAIR,
    label="Through Pair",
    is_reviewed=True,
    is_manual=True,
)

INVALID_STATUS = JointStatus(
    code=JointStatusCode.INVALID,
    label="Invalid Treatment",
    is_reviewed=True,
    is_manual=False,
)


def joint_status_from_saved_treatment(
    saved_treatment,
) -> JointStatus:
    """
    Return display/review status for persistent treatment data.

    saved_treatment follows the joint-treatment store format:

        None

    or:

        (
            mode,
            through_layout_ids,
        )

    A missing record means the joint has never been explicitly
    reviewed.

    The legacy persistence value "both_coped" is presented to
    users as "Both Mitered".
    """

    if saved_treatment is None:
        return UNREVIEWED_STATUS

    try:
        mode, through_layout_ids = (
            saved_treatment
        )

    except (
        TypeError,
        ValueError,
    ):
        return INVALID_STATUS

    mode_value = str(
        getattr(
            mode,
            "value",
            mode,
        )
    ).strip()

    if mode_value == "auto":
        return AUTOMATIC_STATUS

    if mode_value == "member_through":
        return MEMBER_THROUGH_STATUS

    if mode_value == "both_coped":
        return BOTH_MITERED_STATUS

    if mode_value == "both_mitered":
        return BOTH_MITERED_STATUS

    if mode_value == "through_pair":
        return THROUGH_PAIR_STATUS

    return INVALID_STATUS
