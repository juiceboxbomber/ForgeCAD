"""Tests for the production ForgeCAD Undo/Redo recompute observer."""

import importlib
import sys
import types


class FakeNode:
    pass


class FakeMember:
    def __init__(
        self,
        linked=True,
    ):
        self.MemberID = "M001"

        self.StartNode = (
            FakeNode()
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
    def __init__(
        self,
    ):
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


# ---------------------------------------------------------------------------
# FreeCAD test doubles
# ---------------------------------------------------------------------------

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


# Importing forgecad.adapters.freecad first executes that package's
# __init__.py, which imports renderer.py. The renderer imports Part,
# so provide a lightweight Part module for normal-Python unit tests.
fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


observer_module = importlib.import_module(
    "forgecad.adapters.freecad.undo_redo_observer"
)


def test_undo_touches_linked_members_then_recomputes():
    linked = FakeMember(
        linked=True
    )

    unlinked = FakeMember(
        linked=False
    )

    unrelated = FakeUnrelated()

    document = FakeDocument(
        [
            linked,
            unlinked,
            unrelated,
        ]
    )

    observer = (
        observer_module.ForgeCADUndoRedoObserver()
    )

    observer.slotUndoDocument(
        document
    )

    assert linked.touch_count == 1

    assert unlinked.touch_count == 0

    assert unrelated.touch_count == 0

    assert document.recompute_count == 1


def test_redo_touches_linked_members_then_recomputes():
    member = FakeMember(
        linked=True
    )

    document = FakeDocument(
        [
            member,
        ]
    )

    observer = (
        observer_module.ForgeCADUndoRedoObserver()
    )

    observer.slotRedoDocument(
        document
    )

    assert member.touch_count == 1

    assert document.recompute_count == 1


def test_no_linked_members_does_not_force_recompute():
    member = FakeMember(
        linked=False
    )

    document = FakeDocument(
        [
            member,
        ]
    )

    observer = (
        observer_module.ForgeCADUndoRedoObserver()
    )

    observer.slotUndoDocument(
        document
    )

    assert member.touch_count == 0

    assert document.recompute_count == 0


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
