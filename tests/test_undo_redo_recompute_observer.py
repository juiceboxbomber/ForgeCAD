"""Tests for ForgeCAD post-Undo/Redo dependency refresh."""

import importlib
import sys
import types


class FakeMember:
    def __init__(
        self,
        linked=True,
    ):
        self.MemberID = "M001"
        self.StartNode = (
            object()
            if linked
            else None
        )
        self.EndNode = None
        self.touch_count = 0

    def touch(
        self,
    ):
        self.touch_count += 1


class FakeUnrelated:
    pass


class FakeDocument:
    def __init__(
        self,
        objects,
    ):
        self.Objects = list(
            objects
        )
        self.recompute_count = 0

    def recompute(
        self,
    ):
        self.recompute_count += 1


fake_freecad = types.ModuleType(
    "FreeCAD"
)

registered = []

fake_freecad.addDocumentObserver = (
    lambda observer: registered.append(
        observer
    )
)

fake_freecad.removeDocumentObserver = (
    lambda observer: registered.remove(
        observer
    )
)

sys.modules[
    "FreeCAD"
] = fake_freecad


fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


observer_module = importlib.import_module(
    "forgecad.adapters.freecad.undo_redo_observer"
)


def test_refresh_members_touches_only_linked_members():
    linked = FakeMember(
        linked=True
    )

    unlinked = FakeMember(
        linked=False
    )

    document = FakeDocument(
        [
            linked,
            unlinked,
        ]
    )

    touched = (
        observer_module.refresh_parametric_members(
            document
        )
    )

    assert touched == (
        linked,
    )

    assert linked.touch_count == 1
    assert unlinked.touch_count == 0
    assert document.recompute_count == 1


def test_undo_redo_rebuilds_joint_markers_after_member_refresh():
    member = FakeMember(
        linked=True
    )

    document = FakeDocument(
        [
            member,
        ]
    )

    events = []

    original_members = (
        observer_module.refresh_parametric_members
    )

    original_markers = (
        observer_module.rebuild_disposable_joint_markers
    )

    observer_module.refresh_parametric_members = (
        lambda current_document: events.append(
            "members"
        )
        or (
            member,
        )
    )

    observer_module.rebuild_disposable_joint_markers = (
        lambda current_document: events.append(
            "markers"
        )
        or (
            "J001",
        )
    )

    try:
        result = (
            observer_module.refresh_after_undo_redo(
                document
            )
        )

    finally:
        observer_module.refresh_parametric_members = (
            original_members
        )

        observer_module.rebuild_disposable_joint_markers = (
            original_markers
        )

    assert events == [
        "members",
        "markers",
    ]

    assert result == (
        (
            member,
        ),
        (
            "J001",
        ),
    )


def test_observer_uses_combined_post_transaction_refresh():
    document = FakeDocument(
        []
    )

    events = []

    original_refresh = (
        observer_module.refresh_after_undo_redo
    )

    observer_module.refresh_after_undo_redo = (
        lambda current_document: events.append(
            current_document
        )
        or (
            (),
            (),
        )
    )

    try:
        observer = (
            observer_module.ForgeCADUndoRedoObserver()
        )

        observer.slotRedoDocument(
            document
        )

    finally:
        observer_module.refresh_after_undo_redo = (
            original_refresh
        )

    assert events == [
        document
    ]


def test_registration_is_idempotent():
    observer_module._OBSERVER = None
    registered.clear()

    first = (
        observer_module.register_undo_redo_observer()
    )

    second = (
        observer_module.register_undo_redo_observer()
    )

    assert first is second

    assert registered == [
        first
    ]

    assert (
        observer_module.unregister_undo_redo_observer()
        is True
    )

    assert registered == []
    assert observer_module._OBSERVER is None
