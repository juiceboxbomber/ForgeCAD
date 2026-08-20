"""Tests for ForgeCAD joint fabrication validation."""

from forgecad.services.joint_status import (
    AUTOMATIC_STATUS,
    BOTH_MITERED_STATUS,
    INVALID_STATUS,
    MEMBER_THROUGH_STATUS,
    THROUGH_PAIR_STATUS,
    UNREVIEWED_STATUS,
)
from forgecad.services.joint_validation import (
    JointValidationCode,
    validate_joint_status,
)


def test_unreviewed_joint_is_not_ready():
    validation = validate_joint_status(
        UNREVIEWED_STATUS
    )

    assert (
        validation.code
        == JointValidationCode.UNREVIEWED
    )

    assert validation.is_valid
    assert not validation.is_ready


def test_invalid_treatment_is_not_valid():
    validation = validate_joint_status(
        INVALID_STATUS
    )

    assert (
        validation.code
        == JointValidationCode.INVALID_TREATMENT
    )

    assert not validation.is_valid
    assert not validation.is_ready


def test_automatic_joint_is_ready():
    validation = validate_joint_status(
        AUTOMATIC_STATUS
    )

    assert (
        validation.code
        == JointValidationCode.READY
    )

    assert validation.is_valid
    assert validation.is_ready


def test_member_through_joint_is_ready():
    validation = validate_joint_status(
        MEMBER_THROUGH_STATUS
    )

    assert validation.is_valid
    assert validation.is_ready


def test_both_mitered_joint_is_ready():
    validation = validate_joint_status(
        BOTH_MITERED_STATUS
    )

    assert validation.is_valid
    assert validation.is_ready


def test_through_pair_joint_is_ready():
    validation = validate_joint_status(
        THROUGH_PAIR_STATUS
    )

    assert validation.is_valid
    assert validation.is_ready
    