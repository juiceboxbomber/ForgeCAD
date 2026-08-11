"""Visual presentation helpers for ForgeCAD joint status."""

from dataclasses import dataclass

from forgecad.services.joint_status import (
    JointStatus,
    JointStatusCode,
)


@dataclass(
    frozen=True,
    slots=True,
)
class JointStatusVisual:
    """Display information for one joint review state."""

    code: str
    symbol: str
    category: str


UNREVIEWED_VISUAL = JointStatusVisual(
    code="unreviewed",
    symbol="[ ]",
    category="attention",
)

AUTOMATIC_VISUAL = JointStatusVisual(
    code="automatic",
    symbol="[A]",
    category="automatic",
)

MANUAL_VISUAL = JointStatusVisual(
    code="manual",
    symbol="[M]",
    category="manual",
)

INVALID_VISUAL = JointStatusVisual(
    code="invalid",
    symbol="[!]",
    category="attention",
)


def joint_status_visual(
    status: JointStatus,
) -> JointStatusVisual:
    """Return visual presentation data for a joint status."""

    if (
        status.code
        == JointStatusCode.UNREVIEWED
    ):
        return UNREVIEWED_VISUAL

    if (
        status.code
        == JointStatusCode.INVALID
    ):
        return INVALID_VISUAL

    if (
        status.code
        == JointStatusCode.AUTOMATIC
    ):
        return AUTOMATIC_VISUAL

    if status.is_manual:
        return MANUAL_VISUAL

    return INVALID_VISUAL


def joint_status_label(
    joint_id,
    status: JointStatus,
) -> str:
    """Return a tree label containing visual review status."""

    visual = joint_status_visual(
        status
    )

    return (
        f"{visual.symbol} "
        f"{joint_id} - "
        f"{status.label}"
    )
