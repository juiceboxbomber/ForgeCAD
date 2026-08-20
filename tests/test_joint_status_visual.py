"""Tests for ForgeCAD joint-status visual presentation."""

from forgecad.services.joint_status import (
    AUTOMATIC_STATUS,
    BOTH_MITERED_STATUS,
    INVALID_STATUS,
    MEMBER_THROUGH_STATUS,
    THROUGH_PAIR_STATUS,
    UNREVIEWED_STATUS,
)
from forgecad.services.joint_status_visual import (
    joint_status_label,
    joint_status_visual,
)


def test_unreviewed_visual():
    visual = joint_status_visual(
        UNREVIEWED_STATUS
    )

    assert visual.symbol == "[ ]"
    assert visual.category == "attention"


def test_automatic_visual():
    visual = joint_status_visual(
        AUTOMATIC_STATUS
    )

    assert visual.symbol == "[A]"
    assert visual.category == "automatic"


def test_member_through_visual_is_manual():
    visual = joint_status_visual(
        MEMBER_THROUGH_STATUS
    )

    assert visual.symbol == "[M]"
    assert visual.category == "manual"


def test_both_mitered_visual_is_manual():
    visual = joint_status_visual(
        BOTH_MITERED_STATUS
    )

    assert visual.symbol == "[M]"
    assert visual.category == "manual"


def test_through_pair_visual_is_manual():
    visual = joint_status_visual(
        THROUGH_PAIR_STATUS
    )

    assert visual.symbol == "[M]"
    assert visual.category == "manual"


def test_invalid_visual_needs_attention():
    visual = joint_status_visual(
        INVALID_STATUS
    )

    assert visual.symbol == "[!]"
    assert visual.category == "attention"


def test_unreviewed_tree_label():
    label = joint_status_label(
        "J001",
        UNREVIEWED_STATUS,
    )

    assert (
        label
        == "[ ] J001 - Unreviewed"
    )


def test_manual_tree_label():
    label = joint_status_label(
        "J014",
        BOTH_MITERED_STATUS,
    )

    assert (
        label
        == "[M] J014 - Both Mitered"
    )


def test_automatic_tree_label():
    label = joint_status_label(
        "J027",
        AUTOMATIC_STATUS,
    )

    assert (
        label
        == "[A] J027 - Automatic"
    )


def test_invalid_tree_label():
    label = joint_status_label(
        "J003",
        INVALID_STATUS,
    )

    assert (
        label
        == "[!] J003 - Invalid Treatment"
    )
    