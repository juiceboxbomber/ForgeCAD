"""Builder-facing decision model for ForgeCAD joints."""

from dataclasses import dataclass
from enum import Enum

from forgecad.fabrication import (
    Joint,
)
from forgecad.services.joint_member_roles import (
    identify_member_roles,
)


class JointDecisionKind(Enum):
    """Describe whether ForgeCAD can resolve a joint automatically."""

    AUTOMATIC = "automatic"
    NEEDS_DECISION = "needs_decision"


@dataclass(frozen=True, slots=True)
class JointDecision:
    """Describe how ForgeCAD should present one joint to the builder."""

    kind: JointDecisionKind
    reason: str

    @property
    def is_automatic(self) -> bool:
        """Return True when ForgeCAD can handle the joint automatically."""

        return (
            self.kind
            is JointDecisionKind.AUTOMATIC
        )

    @property
    def needs_decision(self) -> bool:
        """Return True when builder input is required."""

        return (
            self.kind
            is JointDecisionKind.NEEDS_DECISION
        )


def decision_for_joint(
    joint: Joint,
) -> JointDecision:
    """
    Decide whether ForgeCAD can safely handle a joint automatically.

    Straight-through joints have an obvious structural path and can
    proceed automatically.

    Ambiguous multi-member joints should ask the builder rather than
    guessing which tubes are intended to continue through the joint.
    """

    roles = identify_member_roles(
        joint
    )

    if roles.has_through_pair:
        return JointDecision(
            kind=JointDecisionKind.AUTOMATIC,
            reason="Straight-through path identified.",
        )

    if joint.member_count <= 2:
        return JointDecision(
            kind=JointDecisionKind.AUTOMATIC,
            reason="Simple joint.",
        )

    return JointDecision(
        kind=JointDecisionKind.NEEDS_DECISION,
        reason="Choose which tubes continue through the joint.",
    )
