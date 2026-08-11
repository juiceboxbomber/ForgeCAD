"""Tests for the ForgeCAD Joint Review Summary command."""

import sys
import types


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecadgui = types.ModuleType(
    "FreeCADGui"
)

fake_part = types.ModuleType(
    "Part"
)

fake_pyside = types.ModuleType(
    "PySide"
)

fake_qtgui = types.ModuleType(
    "QtGui"
)

fake_pyside.QtGui = (
    fake_qtgui
)

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = fake_freecadgui

sys.modules[
    "Part"
] = fake_part

sys.modules[
    "PySide"
] = fake_pyside

sys.modules[
    "PySide.QtGui"
] = fake_qtgui


from forgecad.adapters.freecad.commands.joint_review_summary import (
    summary_text,
    summary_title,
)


class FakeSummary:
    """Minimal JointReviewSummary-like object."""

    def __init__(
        self,
        total_joints,
        reviewed_joints,
        unreviewed_joints,
        automatic_treatments,
        manual_treatments,
        invalid_treatments,
        attention_joints,
        review_percent,
    ):
        self.total_joints = (
            total_joints
        )

        self.reviewed_joints = (
            reviewed_joints
        )

        self.unreviewed_joints = (
            unreviewed_joints
        )

        self.automatic_treatments = (
            automatic_treatments
        )

        self.manual_treatments = (
            manual_treatments
        )

        self.invalid_treatments = (
            invalid_treatments
        )

        self.attention_joints = (
            attention_joints
        )

        self.review_percent = (
            review_percent
        )


def test_summary_text_contains_total():
    summary = FakeSummary(
        total_joints=12,
        reviewed_joints=7,
        unreviewed_joints=5,
        automatic_treatments=2,
        manual_treatments=5,
        invalid_treatments=0,
        attention_joints=5,
        review_percent=(
            58.333333
        ),
    )

    text = summary_text(
        summary
    )

    assert (
        "Total Joints: 12"
        in text
    )


def test_summary_text_contains_review_counts():
    summary = FakeSummary(
        total_joints=12,
        reviewed_joints=7,
        unreviewed_joints=5,
        automatic_treatments=2,
        manual_treatments=5,
        invalid_treatments=0,
        attention_joints=5,
        review_percent=58.3,
    )

    text = summary_text(
        summary
    )

    assert (
        "Reviewed: 7"
        in text
    )

    assert (
        "Unreviewed: 5"
        in text
    )


def test_summary_text_contains_treatment_counts():
    summary = FakeSummary(
        total_joints=12,
        reviewed_joints=7,
        unreviewed_joints=5,
        automatic_treatments=2,
        manual_treatments=5,
        invalid_treatments=1,
        attention_joints=6,
        review_percent=58.3,
    )

    text = summary_text(
        summary
    )

    assert (
        "Automatic: 2"
        in text
    )

    assert (
        "Manual Treatments: 5"
        in text
    )

    assert (
        "Invalid: 1"
        in text
    )

    assert (
        "Needs Attention: 6"
        in text
    )


def test_summary_text_formats_review_percent():
    summary = FakeSummary(
        total_joints=3,
        reviewed_joints=2,
        unreviewed_joints=1,
        automatic_treatments=1,
        manual_treatments=1,
        invalid_treatments=0,
        attention_joints=1,
        review_percent=(
            66.666666
        ),
    )

    assert (
        "Review Complete: 66.7%"
        in summary_text(
            summary
        )
    )


def test_normal_summary_title():
    summary = FakeSummary(
        total_joints=5,
        reviewed_joints=3,
        unreviewed_joints=2,
        automatic_treatments=1,
        manual_treatments=2,
        invalid_treatments=0,
        attention_joints=2,
        review_percent=60.0,
    )

    assert (
        summary_title(
            summary
        )
        == "Joint Review Summary"
    )


def test_complete_summary_title():
    summary = FakeSummary(
        total_joints=5,
        reviewed_joints=5,
        unreviewed_joints=0,
        automatic_treatments=2,
        manual_treatments=3,
        invalid_treatments=0,
        attention_joints=0,
        review_percent=100.0,
    )

    assert (
        summary_title(
            summary
        )
        == "Joint Review Complete"
    )


def test_empty_summary_uses_normal_title():
    summary = FakeSummary(
        total_joints=0,
        reviewed_joints=0,
        unreviewed_joints=0,
        automatic_treatments=0,
        manual_treatments=0,
        invalid_treatments=0,
        attention_joints=0,
        review_percent=0.0,
    )

    assert (
        summary_title(
            summary
        )
        == "Joint Review Summary"
    )
    