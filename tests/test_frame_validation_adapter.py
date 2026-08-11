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
from forgecad.services.joint_status import (
    AUTOMATIC_STATUS,
    INVALID_STATUS,
    MEMBER_THROUGH_STATUS,
    UNREVIEWED_STATUS,
)


class FakeDocumentJointStatus:
    """Minimal document joint-status item."""

    def __init__(
        self,
        status,
    ):
        self.status = status


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


def test_empty_document_is_not_ready(
    monkeypatch,
):
    monkeypatch.setattr(
        frame_validation_adapter,
        "joint_statuses_for_document",
        lambda document: (),
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
    