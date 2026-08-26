"""Tests for ForgeCAD Undo/Redo observer behavior."""

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


def test_parametric_member_detection_is_preserved():
    linked = FakeMember(
        linked=True
    )

    unlinked = FakeMember(
        linked=False
    )

    assert observer_module.is_parametric_tube_member(
        linked
    )

    assert not observer_module.is_parametric_tube_member(
        unlinked
    )

    assert not observer_module.is_parametric_tube_member(
        object()
    )


def test_post_undo_redo_member_refresh_does_not_mutate_document():
    linked = FakeMember(
        linked=True
    )

    document = FakeDocument(
        [
            linked,
        ]
    )

    result = (
        observer_module.refresh_parametric_members(
            document
        )
    )

    assert result == ()
    assert linked.touch_count == 0
    assert document.recompute_count == 0


def test_post_undo_redo_marker_refresh_is_non_mutating():
    document = FakeDocument(
        []
    )

    result = (
        observer_module.rebuild_disposable_joint_markers(
            document
        )
    )

    assert result == ()
    assert document.recompute_count == 0


def test_combined_post_undo_redo_refresh_is_non_mutating():
    member = FakeMember(
        linked=True
    )

    document = FakeDocument(
        [
            member,
        ]
    )

    result = (
        observer_module.refresh_after_undo_redo(
            document
        )
    )

    assert result == (
        (),
        (),
    )

    assert member.touch_count == 0
    assert document.recompute_count == 0


def test_observer_calls_non_mutating_refresh_for_undo_and_redo():
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

        observer.slotUndoDocument(
            document
        )

        observer.slotRedoDocument(
            document
        )

    finally:
        observer_module.refresh_after_undo_redo = (
            original_refresh
        )

    assert events == [
        document,
        document,
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
