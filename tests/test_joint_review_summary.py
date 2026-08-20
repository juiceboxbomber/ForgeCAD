"""Tests for ForgeCAD frame-level joint review summaries."""

import pytest

from forgecad.services.joint_review_summary import (
    summarize_joint_statuses,
)
from forgecad.services.joint_status import (
    joint_status_from_saved_treatment,
)


def status(
    saved_treatment,
):
    """Build a status from stored treatment data."""

    return joint_status_from_saved_treatment(
        saved_treatment
    )


def test_empty_summary():
    summary = (
        summarize_joint_statuses(
            []
        )
    )

    assert summary.total_joints == 0
    assert summary.reviewed_joints == 0
    assert summary.unreviewed_joints == 0
    assert summary.manual_treatments == 0
    assert summary.automatic_treatments == 0
    assert summary.invalid_treatments == 0

    assert not summary.all_reviewed

    assert (
        summary.review_fraction
        == pytest.approx(
            0.0
        )
    )

    assert (
        summary.review_percent
        == pytest.approx(
            0.0
        )
    )


def test_all_unreviewed():
    summary = (
        summarize_joint_statuses(
            [
                status(None),
                status(None),
                status(None),
            ]
        )
    )

    assert summary.total_joints == 3
    assert summary.reviewed_joints == 0
    assert summary.unreviewed_joints == 3
    assert summary.manual_treatments == 0

    assert not summary.all_reviewed


def test_reviewed_automatic_is_counted():
    summary = (
        summarize_joint_statuses(
            [
                status(
                    (
                        "auto",
                        (),
                    )
                ),
            ]
        )
    )

    assert summary.total_joints == 1
    assert summary.reviewed_joints == 1
    assert summary.unreviewed_joints == 0
    assert summary.automatic_treatments == 1
    assert summary.manual_treatments == 0

    assert summary.all_reviewed


def test_manual_treatments_are_counted():
    summary = (
        summarize_joint_statuses(
            [
                status(
                    (
                        "member_through",
                        (
                            "L001",
                        ),
                    )
                ),
                status(
                    (
                        "both_coped",
                        (),
                    )
                ),
                status(
                    (
                        "through_pair",
                        (
                            "L002",
                            "L003",
                        ),
                    )
                ),
            ]
        )
    )

    assert summary.total_joints == 3
    assert summary.reviewed_joints == 3
    assert summary.manual_treatments == 3
    assert summary.automatic_treatments == 0

    assert summary.all_reviewed


def test_mixed_review_state():
    summary = (
        summarize_joint_statuses(
            [
                status(None),
                status(
                    (
                        "auto",
                        (),
                    )
                ),
                status(
                    (
                        "both_coped",
                        (),
                    )
                ),
                status(None),
            ]
        )
    )

    assert summary.total_joints == 4
    assert summary.reviewed_joints == 2
    assert summary.unreviewed_joints == 2
    assert summary.manual_treatments == 1
    assert summary.automatic_treatments == 1

    assert not summary.all_reviewed

    assert (
        summary.review_fraction
        == pytest.approx(
            0.5
        )
    )

    assert (
        summary.review_percent
        == pytest.approx(
            50.0
        )
    )


def test_invalid_treatment_is_reviewed_but_flagged():
    summary = (
        summarize_joint_statuses(
            [
                status(
                    (
                        "unknown",
                        (),
                    )
                ),
            ]
        )
    )

    assert summary.total_joints == 1
    assert summary.reviewed_joints == 1
    assert summary.unreviewed_joints == 0
    assert summary.invalid_treatments == 1

    assert summary.all_reviewed


def test_review_percentage():
    summary = (
        summarize_joint_statuses(
            [
                status(
                    (
                        "auto",
                        (),
                    )
                ),
                status(
                    (
                        "member_through",
                        (
                            "L001",
                        ),
                    )
                ),
                status(None),
                status(None),
            ]
        )
    )

    assert (
        summary.review_percent
        == pytest.approx(
            50.0
        )
    )


def test_complete_mixed_treatments():
    summary = (
        summarize_joint_statuses(
            [
                status(
                    (
                        "auto",
                        (),
                    )
                ),
                status(
                    (
                        "member_through",
                        (
                            "L001",
                        ),
                    )
                ),
                status(
                    (
                        "both_coped",
                        (),
                    )
                ),
                status(
                    (
                        "through_pair",
                        (
                            "L002",
                            "L003",
                        ),
                    )
                ),
            ]
        )
    )

    assert summary.total_joints == 4
    assert summary.reviewed_joints == 4
    assert summary.unreviewed_joints == 0
    assert summary.manual_treatments == 3
    assert summary.automatic_treatments == 1
    assert summary.invalid_treatments == 0

    assert summary.all_reviewed

    assert (
        summary.review_percent
        == pytest.approx(
            100.0
        )
    )
    