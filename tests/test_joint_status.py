"""Tests for ForgeCAD joint review status."""

from forgecad.fabrication.joint_treatment import (
    JointTreatmentMode,
)
from forgecad.services.joint_status import (
    JointStatusCode,
    joint_status_from_saved_treatment,
)


def test_missing_treatment_is_unreviewed():
    status = (
        joint_status_from_saved_treatment(
            None
        )
    )

    assert (
        status.code
        == JointStatusCode.UNREVIEWED
    )

    assert not status.is_reviewed

    assert not status.is_manual

    assert status.label == (
        "Unreviewed"
    )


def test_saved_auto_is_reviewed_automatic():
    status = (
        joint_status_from_saved_treatment(
            (
                "auto",
                (),
            )
        )
    )

    assert (
        status.code
        == JointStatusCode.AUTOMATIC
    )

    assert status.is_reviewed

    assert not status.is_manual

    assert status.label == (
        "Automatic"
    )


def test_member_through_is_manual():
    status = (
        joint_status_from_saved_treatment(
            (
                "member_through",
                (
                    "L001",
                ),
            )
        )
    )

    assert (
        status.code
        == JointStatusCode.MEMBER_THROUGH
    )

    assert status.is_reviewed

    assert status.is_manual

    assert status.label == (
        "Member Through"
    )


def test_legacy_both_coped_displays_as_both_mitered():
    status = (
        joint_status_from_saved_treatment(
            (
                "both_coped",
                (),
            )
        )
    )

    assert (
        status.code
        == JointStatusCode.BOTH_MITERED
    )

    assert status.label == (
        "Both Mitered"
    )

    assert status.is_manual


def test_future_both_mitered_value_is_also_supported():
    status = (
        joint_status_from_saved_treatment(
            (
                "both_mitered",
                (),
            )
        )
    )

    assert (
        status.code
        == JointStatusCode.BOTH_MITERED
    )


def test_through_pair_is_manual():
    status = (
        joint_status_from_saved_treatment(
            (
                "through_pair",
                (
                    "L001",
                    "L002",
                ),
            )
        )
    )

    assert (
        status.code
        == JointStatusCode.THROUGH_PAIR
    )

    assert status.is_reviewed

    assert status.is_manual

    assert status.label == (
        "Through Pair"
    )


def test_enum_value_is_supported():
    status = (
        joint_status_from_saved_treatment(
            (
                JointTreatmentMode.MEMBER_THROUGH,
                (
                    "L001",
                ),
            )
        )
    )

    assert (
        status.code
        == JointStatusCode.MEMBER_THROUGH
    )


def test_unknown_mode_is_invalid():
    status = (
        joint_status_from_saved_treatment(
            (
                "something_unknown",
                (),
            )
        )
    )

    assert (
        status.code
        == JointStatusCode.INVALID
    )

    assert status.is_reviewed

    assert not status.is_manual

    assert status.label == (
        "Invalid Treatment"
    )


def test_malformed_saved_data_is_invalid():
    status = (
        joint_status_from_saved_treatment(
            (
                "auto",
            )
        )
    )

    assert (
        status.code
        == JointStatusCode.INVALID
    )


def test_extra_saved_data_is_invalid():
    status = (
        joint_status_from_saved_treatment(
            (
                "auto",
                (),
                "extra",
            )
        )
    )

    assert (
        status.code
        == JointStatusCode.INVALID
    )
    