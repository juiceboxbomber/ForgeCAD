"""Tests for ForgeCAD FreeCAD frame validation adapter."""

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

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = fake_freecadgui

sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad import (
    frame_validation_adapter,
)
from forgecad.services.frame_validation import (
    validate_frame_joint_statuses,
)
from forgecad.services.joint_status import (
    AUTOMATIC_STATUS,
    INVALID_STATUS,
    MEMBER_THROUGH_STATUS,
    UNREVIEWED_STATUS,
)
from forgecad.services.member_end_validation import (
    MemberEndValidation,
    MemberEndValidationCode,
    MemberEndKey,
)


class FakeDocumentJointStatus:
    """Minimal document joint-status item."""

    def __init__(
        self,
        status,
    ):
        self.status = status


class FakeMember:
    pass


def no_member_end_conflicts(
    monkeypatch,
):
    monkeypatch.setattr(
        frame_validation_adapter,
        "member_end_validations_for_document",
        lambda document: (),
    )


def test_all_reviewed_document_is_ready(
    monkeypatch,
):
    monkeypatch.setattr(
        frame_validation_adapter,
        "joint_statuses_for_document",
        lambda document: (
            FakeDocumentJointStatus(
                AUTOMATIC_STATUS
            ),
            FakeDocumentJointStatus(
                MEMBER_THROUGH_STATUS
            ),
        ),
    )

    no_member_end_conflicts(
        monkeypatch
    )

    result = (
        frame_validation_adapter
        .frame_validation_for_document(
            object()
        )
    )

    assert result.is_ready
    assert result.total_joints == 2
    assert result.ready_joints == 2
    assert result.not_ready_joints == 0
    assert result.invalid_joints == 0
    assert result.conflict_count == 0


def test_unreviewed_document_is_not_ready(
    monkeypatch,
):
    monkeypatch.setattr(
        frame_validation_adapter,
        "joint_statuses_for_document",
        lambda document: (
            FakeDocumentJointStatus(
                AUTOMATIC_STATUS
            ),
            FakeDocumentJointStatus(
                UNREVIEWED_STATUS
            ),
        ),
    )

    no_member_end_conflicts(
        monkeypatch
    )

    result = (
        frame_validation_adapter
        .frame_validation_for_document(
            object()
        )
    )

    assert not result.is_ready
    assert result.total_joints == 2
    assert result.ready_joints == 1
    assert result.not_ready_joints == 1
    assert result.invalid_joints == 0
    assert result.conflict_count == 0


def test_invalid_document_is_not_ready(
    monkeypatch,
):
    monkeypatch.setattr(
        frame_validation_adapter,
        "joint_statuses_for_document",
        lambda document: (
            FakeDocumentJointStatus(
                MEMBER_THROUGH_STATUS
            ),
            FakeDocumentJointStatus(
                INVALID_STATUS
            ),
        ),
    )

    no_member_end_conflicts(
        monkeypatch
    )

    result = (
        frame_validation_adapter
        .frame_validation_for_document(
            object()
        )
    )

    assert not result.is_ready
    assert result.total_joints == 2
    assert result.ready_joints == 1
    assert result.not_ready_joints == 1
    assert result.invalid_joints == 1
    assert result.conflict_count == 0


def test_empty_document_is_not_ready(
    monkeypatch,
):
    monkeypatch.setattr(
        frame_validation_adapter,
        "joint_statuses_for_document",
        lambda document: (),
    )

    no_member_end_conflicts(
        monkeypatch
    )

    result = (
        frame_validation_adapter
        .frame_validation_for_document(
            object()
        )
    )

    assert not result.is_ready
    assert result.total_joints == 0
    assert result.ready_joints == 0
    assert result.not_ready_joints == 0
    assert result.invalid_joints == 0
    assert result.conflict_count == 0


def test_conflicting_member_end_blocks_ready_frame(
    monkeypatch,
):
    monkeypatch.setattr(
        frame_validation_adapter,
        "joint_statuses_for_document",
        lambda document: (
            FakeDocumentJointStatus(
                AUTOMATIC_STATUS
            ),
            FakeDocumentJointStatus(
                MEMBER_THROUGH_STATUS
            ),
        ),
    )

    conflict = MemberEndValidation(
        key=MemberEndKey(
            member=FakeMember(),
            member_end="start",
        ),
        code=(
            MemberEndValidationCode
            .CONFLICTING_COPES
        ),
        operation_count=2,
        is_valid=False,
    )

    monkeypatch.setattr(
        frame_validation_adapter,
        "member_end_validations_for_document",
        lambda document: (
            conflict,
        ),
    )

    result = (
        frame_validation_adapter
        .frame_validation_for_document(
            object()
        )
    )

    assert result.total_joints == 2
    assert result.ready_joints == 2

    assert result.validation.is_ready

    assert result.conflict_count == 1
    assert not result.is_ready
    