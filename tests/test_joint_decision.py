"""Tests for builder-facing joint decisions."""

from dataclasses import dataclass

from forgecad.fabrication import (
    Joint,
    Node,
)
from forgecad.services.joint_decision import (
    JointDecisionKind,
    decision_for_joint,
)


@dataclass(
    frozen=True,
)
class FakeMember:
    """Minimal member representation needed for joint-role analysis."""

    start: Node
    end: Node


def member(
    start,
    end,
):
    return FakeMember(
        start=start,
        end=end,
    )


def test_straight_through_joint_is_automatic():
    joint_node = Node(
        0.0,
        0.0,
        0.0,
    )

    left = member(
        Node(
            -1000.0,
            0.0,
            0.0,
        ),
        joint_node,
    )

    right = member(
        joint_node,
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    branch = member(
        joint_node,
        Node(
            0.0,
            500.0,
            0.0,
        ),
    )

    decision = decision_for_joint(
        Joint(
            node=joint_node,
            members=[
                left,
                right,
                branch,
            ],
        )
    )

    assert (
        decision.kind
        is JointDecisionKind.AUTOMATIC
    )

    assert decision.is_automatic
    assert not decision.needs_decision


def test_simple_two_member_joint_is_automatic():
    joint_node = Node(
        0.0,
        0.0,
        0.0,
    )

    first = member(
        Node(
            -500.0,
            0.0,
            0.0,
        ),
        joint_node,
    )

    second = member(
        joint_node,
        Node(
            0.0,
            500.0,
            0.0,
        ),
    )

    decision = decision_for_joint(
        Joint(
            node=joint_node,
            members=[
                first,
                second,
            ],
        )
    )

    assert decision.is_automatic


def test_ambiguous_three_member_joint_needs_builder_decision():
    joint_node = Node(
        0.0,
        0.0,
        0.0,
    )

    first = member(
        joint_node,
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        joint_node,
        Node(
            0.0,
            500.0,
            0.0,
        ),
    )

    third = member(
        joint_node,
        Node(
            400.0,
            400.0,
            0.0,
        ),
    )

    decision = decision_for_joint(
        Joint(
            node=joint_node,
            members=[
                first,
                second,
                third,
            ],
        )
    )

    assert (
        decision.kind
        is JointDecisionKind.NEEDS_DECISION
    )

    assert decision.needs_decision
    assert not decision.is_automatic

    assert decision.reason == (
        "Choose which tubes continue through the joint."
    )
