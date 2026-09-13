"""Tests for builder-facing joint decision status integration."""

import sys
import types


fake_freecad = types.ModuleType(
    "FreeCAD"
)

sys.modules[
    "FreeCAD"
] = fake_freecad


fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


from dataclasses import dataclass

from forgecad.fabrication import (
    Joint,
    Node,
)
from forgecad.services.joint_status import (
    AUTOMATIC_STATUS,
    MEMBER_THROUGH_STATUS,
    NEEDS_DECISION_STATUS,
)
from forgecad.adapters.freecad import joint_status_adapter


@dataclass(
    frozen=True,
)
class FakeMember:
    start: Node
    end: Node


def test_unreviewed_straight_through_joint_is_automatic():
    node = Node(
        0.0,
        0.0,
        0.0,
    )

    joint = Joint(
        node=node,
        members=[
            FakeMember(
                Node(
                    -1000.0,
                    0.0,
                    0.0,
                ),
                node,
            ),
            FakeMember(
                node,
                Node(
                    1000.0,
                    0.0,
                    0.0,
                ),
            ),
            FakeMember(
                node,
                Node(
                    0.0,
                    500.0,
                    0.0,
                ),
            ),
        ],
    )

    status = (
        joint_status_adapter.status_for_unreviewed_joint(
            joint
        )
    )

    assert status is AUTOMATIC_STATUS


def test_unreviewed_ambiguous_joint_needs_decision():
    node = Node(
        0.0,
        0.0,
        0.0,
    )

    joint = Joint(
        node=node,
        members=[
            FakeMember(
                node,
                Node(
                    500.0,
                    0.0,
                    0.0,
                ),
            ),
            FakeMember(
                node,
                Node(
                    0.0,
                    500.0,
                    0.0,
                ),
            ),
            FakeMember(
                node,
                Node(
                    400.0,
                    400.0,
                    0.0,
                ),
            ),
        ],
    )

    status = (
        joint_status_adapter.status_for_unreviewed_joint(
            joint
        )
    )

    assert status is NEEDS_DECISION_STATUS
    assert status.needs_attention


def test_saved_builder_treatment_remains_authoritative():
    node = Node(
        0.0,
        0.0,
        0.0,
    )

    joint = Joint(
        node=node,
        members=[],
    )

    original_node_key = (
        joint_status_adapter.node_key
    )

    original_load = (
        joint_status_adapter.load_joint_treatment
    )

    joint_status_adapter.node_key = (
        lambda current_node: "KEY"
    )

    joint_status_adapter.load_joint_treatment = (
        lambda document,
        key: (
            "member_through",
            (),
        )
    )

    try:
        item = (
            joint_status_adapter.joint_status_for_document_joint(
                object(),
                joint,
            )
        )
    finally:
        joint_status_adapter.node_key = (
            original_node_key
        )

        joint_status_adapter.load_joint_treatment = (
            original_load
        )

    assert item.status is MEMBER_THROUGH_STATUS
