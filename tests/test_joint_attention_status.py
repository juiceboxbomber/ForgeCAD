"""Tests for ForgeCAD joint attention status."""

from forgecad.services.joint_review_summary import (
    summarize_joint_statuses,
)
from forgecad.services.joint_status import (
    AUTOMATIC_STATUS,
    BOTH_MITERED_STATUS,
    INVALID_STATUS,
    MEMBER_THROUGH_STATUS,
    THROUGH_PAIR_STATUS,
    UNREVIEWED_STATUS,
)


def test_unreviewed_needs_attention():
    assert (
        UNREVIEWED_STATUS.needs_attention
    )


def test_invalid_needs_attention():
    assert (
        INVALID_STATUS.needs_attention
    )


def test_automatic_does_not_need_attention():
    assert not (
        AUTOMATIC_STATUS.needs_attention
    )


def test_member_through_does_not_need_attention():
    assert not (
        MEMBER_THROUGH_STATUS.needs_attention
    )


def test_both_mitered_does_not_need_attention():
    assert not (
        BOTH_MITERED_STATUS.needs_attention
    )


def test_through_pair_does_not_need_attention():
    assert not (
        THROUGH_PAIR_STATUS.needs_attention
    )


def test_summary_counts_attention_items():
    summary = summarize_joint_statuses(
        (
            UNREVIEWED_STATUS,
            AUTOMATIC_STATUS,
            BOTH_MITERED_STATUS,
            INVALID_STATUS,
        )
    )

    assert (
        summary.total_joints
        == 4
    )

    assert (
        summary.attention_joints
        == 2
    )

    assert (
        summary.has_attention_items
    )


def test_summary_without_attention_items():
    summary = summarize_joint_statuses(
        (
            AUTOMATIC_STATUS,
            MEMBER_THROUGH_STATUS,
            BOTH_MITERED_STATUS,
            THROUGH_PAIR_STATUS,
        )
    )

    assert (
        summary.attention_joints
        == 0
    )

    assert not (
        summary.has_attention_items
    )
    