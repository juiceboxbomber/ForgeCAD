"""Tests for the FreeCAD joint-status adapter."""

import sys
import types


sys.modules[
    "FreeCAD"
] = types.ModuleType(
    "FreeCAD"
)

sys.modules[
    "FreeCADGui"
] = types.ModuleType(
    "FreeCADGui"
)

sys.modules[
    "Part"
] = types.ModuleType(
    "Part"
)


from forgecad.adapters.freecad import (
    joint_status_adapter,
)
from forgecad.services.joint_status import (
    JointStatusCode,
)


class FakeVector:
    """Minimal FreeCAD-like vector."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


class FakeMemberObject:
    """Minimal generated ForgeCAD member."""

    def __init__(
        self,
        member_id,
        start,
        end,
        tube_profile="1.750 x .120 DOM",
    ):
        self.MemberID = member_id
        self.TubeProfile = tube_profile
        self.StartPoint = start
        self.EndPoint = end


class FakeGroup:
    """Minimal FreeCAD document group."""

    def __init__(
        self,
        objects=None,
    ):
        self.Group = list(
            objects
            or []
        )


class FakeDocument:
    """Minimal document supporting object lookup."""

    def __init__(
        self,
        frame_objects=None,
    ):
        self.objects = {
            "ForgeCADFrame": FakeGroup(
                frame_objects
                or []
            )
        }

    def getObject(
        self,
        name,
    ):
        return self.objects.get(
            name
        )


def make_corner_document():
    """Return a document containing one two-member corner."""

    center = FakeVector(
        0,
        0,
        0,
    )

    first = FakeMemberObject(
        "M001",
        center,
        FakeVector(
            500,
            0,
            0,
        ),
    )

    second = FakeMemberObject(
        "M002",
        center,
        FakeVector(
            0,
            500,
            0,
        ),
    )

    return FakeDocument(
        [
            first,
            second,
        ]
    )


def make_two_joint_document():
    """Return a three-member chain containing two joints."""

    a = FakeVector(
        0,
        0,
        0,
    )

    b = FakeVector(
        500,
        0,
        0,
    )

    c = FakeVector(
        500,
        500,
        0,
    )

    d = FakeVector(
        1000,
        500,
        0,
    )

    first = FakeMemberObject(
        "M001",
        a,
        b,
    )

    second = FakeMemberObject(
        "M002",
        b,
        c,
    )

    third = FakeMemberObject(
        "M003",
        c,
        d,
    )

    return FakeDocument(
        [
            first,
            second,
            third,
        ]
    )


def test_none_document_has_no_joint_statuses():
    assert (
        joint_status_adapter
        .joint_statuses_for_document(
            None
        )
        == ()
    )


def test_empty_frame_has_no_joint_statuses():
    document = FakeDocument()

    assert (
        joint_status_adapter
        .joint_statuses_for_document(
            document
        )
        == ()
    )


def test_corner_document_detects_one_joint(
    monkeypatch,
):
    document = (
        make_corner_document()
    )

    monkeypatch.setattr(
        joint_status_adapter,
        "load_joint_treatment",
        lambda document, key: None,
    )

    statuses = (
        joint_status_adapter
        .joint_statuses_for_document(
            document
        )
    )

    assert len(
        statuses
    ) == 1


def test_missing_saved_treatment_is_automatic_when_joint_is_obvious(
    monkeypatch,
):
    document = (
        make_corner_document()
    )

    monkeypatch.setattr(
        joint_status_adapter,
        "load_joint_treatment",
        lambda document, key: None,
    )

    item = (
        joint_status_adapter
        .joint_statuses_for_document(
            document
        )[
            0
        ]
    )

    assert (
        item.status.code
        == JointStatusCode.AUTOMATIC
    )

    assert item.is_reviewed
    assert not item.is_manual


def test_saved_auto_is_reviewed(
    monkeypatch,
):
    document = (
        make_corner_document()
    )

    monkeypatch.setattr(
        joint_status_adapter,
        "load_joint_treatment",
        lambda document, key: (
            "auto",
            (),
        ),
    )

    item = (
        joint_status_adapter
        .joint_statuses_for_document(
            document
        )[
            0
        ]
    )

    assert (
        item.status.code
        == JointStatusCode.AUTOMATIC
    )

    assert item.is_reviewed
    assert not item.is_manual


def test_saved_miter_is_manual(
    monkeypatch,
):
    document = (
        make_corner_document()
    )

    monkeypatch.setattr(
        joint_status_adapter,
        "load_joint_treatment",
        lambda document, key: (
            "both_coped",
            (),
        ),
    )

    item = (
        joint_status_adapter
        .joint_statuses_for_document(
            document
        )[
            0
        ]
    )

    assert (
        item.status.code
        == JointStatusCode.BOTH_MITERED
    )

    assert item.is_reviewed
    assert item.is_manual


def test_document_joint_has_stable_coordinate_key(
    monkeypatch,
):
    document = (
        make_corner_document()
    )

    monkeypatch.setattr(
        joint_status_adapter,
        "load_joint_treatment",
        lambda document, key: None,
    )

    item = (
        joint_status_adapter
        .joint_statuses_for_document(
            document
        )[
            0
        ]
    )

    assert item.node_key == (
        "0.000000,0.000000,0.000000"
    )


def test_two_joint_document_detects_two_joints(
    monkeypatch,
):
    document = (
        make_two_joint_document()
    )

    monkeypatch.setattr(
        joint_status_adapter,
        "load_joint_treatment",
        lambda document, key: None,
    )

    statuses = (
        joint_status_adapter
        .joint_statuses_for_document(
            document
        )
    )

    assert len(
        statuses
    ) == 2


def test_review_summary_counts_real_document_joints(
    monkeypatch,
):
    document = (
        make_two_joint_document()
    )

    def fake_load(
        document,
        key,
    ):
        if key == (
            "500.000000,"
            "0.000000,"
            "0.000000"
        ):
            return (
                "auto",
                (),
            )

        return None

    monkeypatch.setattr(
        joint_status_adapter,
        "load_joint_treatment",
        fake_load,
    )

    review = (
        joint_status_adapter
        .joint_review_for_document(
            document
        )
    )

    assert (
        review.summary.total_joints
        == 2
    )

    assert (
        review.summary.reviewed_joints
        == 2
    )

    assert (
        review.summary.unreviewed_joints
        == 0
    )

    assert (
        review.summary.automatic_treatments
        == 2
    )

    assert (
        review.summary.all_reviewed
    )


def test_complete_document_review_reports_all_reviewed(
    monkeypatch,
):
    document = (
        make_two_joint_document()
    )

    def fake_load(
        document,
        key,
    ):
        if key == (
            "500.000000,"
            "0.000000,"
            "0.000000"
        ):
            return (
                "member_through",
                (
                    "L001",
                ),
            )

        return (
            "both_coped",
            (),
        )

    monkeypatch.setattr(
        joint_status_adapter,
        "load_joint_treatment",
        fake_load,
    )

    review = (
        joint_status_adapter
        .joint_review_for_document(
            document
        )
    )

    assert (
        review.summary.total_joints
        == 2
    )

    assert (
        review.summary.reviewed_joints
        == 2
    )

    assert (
        review.summary.unreviewed_joints
        == 0
    )

    assert (
        review.summary.manual_treatments
        == 2
    )

    assert (
        review.summary.review_percent
        == 100.0
    )

    assert (
        review.summary.all_reviewed
    )
