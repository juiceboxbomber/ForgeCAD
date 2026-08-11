"""Tests for ForgeCAD frame fabrication validation."""

from forgecad.services.frame_validation import (
    validate_frame_joint_statuses,
)
from forgecad.services.joint_status import (
    AUTOMATIC_STATUS,
    BOTH_MITERED_STATUS,
    INVALID_STATUS,
    MEMBER_THROUGH_STATUS,
    UNREVIEWED_STATUS,
)


def test_empty_frame_is_not_ready():
    validation = validate_frame_joint_statuses(
        []
    )

    assert validation.total_joints == 0
    assert validation.ready_joints == 0
    assert validation.not_ready_joints == 0
    assert validation.invalid_joints == 0

    assert not validation.is_ready


def test_all_reviewed_joints_are_ready():
    validation = validate_frame_joint_statuses(
        [
            AUTOMATIC_STATUS,
            MEMBER_THROUGH_STATUS,
            BOTH_MITERED_STATUS,
        ]
    )

    assert validation.total_joints == 3
    assert validation.ready_joints == 3
    assert validation.not_ready_joints == 0
    assert validation.invalid_joints == 0

    assert validation.is_ready


def test_unreviewed_joint_blocks_frame_readiness():
    validation = validate_frame_joint_statuses(
        [
            AUTOMATIC_STATUS,
            UNREVIEWED_STATUS,
        ]
    )

    assert validation.total_joints == 2
    assert validation.ready_joints == 1
    assert validation.not_ready_joints == 1
    assert validation.invalid_joints == 0

    assert not validation.is_ready


def test_invalid_joint_blocks_frame_readiness():
    validation = validate_frame_joint_statuses(
        [
            BOTH_MITERED_STATUS,
            INVALID_STATUS,
        ]
    )

    assert validation.total_joints == 2
    assert validation.ready_joints == 1
    assert validation.not_ready_joints == 1
    assert validation.invalid_joints == 1

    assert not validation.is_ready


def test_mixed_frame_counts_are_correct():
    validation = validate_frame_joint_statuses(
        [
            AUTOMATIC_STATUS,
            MEMBER_THROUGH_STATUS,
            UNREVIEWED_STATUS,
            INVALID_STATUS,
        ]
    )

    assert validation.total_joints == 4
    assert validation.ready_joints == 2
    assert validation.not_ready_joints == 2
    assert validation.invalid_joints == 1

    assert not validation.is_ready
    