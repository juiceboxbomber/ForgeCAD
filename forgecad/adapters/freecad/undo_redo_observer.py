"""Undo/Redo observer for ForgeCAD FreeCAD documents.

FreeCAD transactions own model restoration. The observer deliberately does
not touch, recompute, create, delete, or rebuild document objects after an
Undo or Redo because any post-transaction document mutation can invalidate
FreeCAD's Redo stack.
"""

import FreeCAD


_OBSERVER = None


def is_parametric_tube_member(
    obj,
):
    """Return True for a straight ForgeCAD member linked to at least one node."""

    if obj is None:
        return False

    if not hasattr(
        obj,
        "MemberID",
    ):
        return False

    start_node = getattr(
        obj,
        "StartNode",
        None,
    )

    end_node = getattr(
        obj,
        "EndNode",
        None,
    )

    return (
        start_node is not None
        or end_node is not None
    )


def refresh_parametric_members(
    document,
):
    """
    Compatibility no-op for the former post-Undo/Redo member refresh.

    FreeCAD transactions restore member state. Touching or recomputing here
    would create a new document modification after Undo and can clear Redo.
    """

    return ()


def rebuild_disposable_joint_markers(
    document,
):
    """
    Compatibility no-op for the former post-Undo/Redo marker rebuild.

    Joint marker changes must be included in the user transaction that
    created or modified the topology. Rebuilding document objects after
    Undo/Redo can invalidate FreeCAD's Redo history.
    """

    return ()


def refresh_after_undo_redo(
    document,
):
    """
    Perform no document mutation after FreeCAD Undo or Redo.

    The return shape is retained for compatibility with existing callers
    and tests while transaction-owned restoration remains authoritative.
    """

    return (
        (),
        (),
    )


class ForgeCADUndoRedoObserver:
    """Observe Undo/Redo without modifying the document history."""

    def __init__(
        self,
    ):
        self._refreshing = False

    def _refresh(
        self,
        document,
    ):
        if self._refreshing:
            return (
                (),
                (),
            )

        self._refreshing = True

        try:
            return refresh_after_undo_redo(
                document
            )
        finally:
            self._refreshing = False

    def slotUndoDocument(
        self,
        document,
    ):
        self._refresh(
            document
        )

    def slotRedoDocument(
        self,
        document,
    ):
        self._refresh(
            document
        )


def register_undo_redo_observer():
    """Register one process-wide ForgeCAD Undo/Redo document observer."""

    global _OBSERVER

    if _OBSERVER is not None:
        return _OBSERVER

    observer = ForgeCADUndoRedoObserver()

    FreeCAD.addDocumentObserver(
        observer
    )

    _OBSERVER = observer

    return observer


def unregister_undo_redo_observer():
    """Remove the registered ForgeCAD Undo/Redo observer, if present."""

    global _OBSERVER

    observer = _OBSERVER

    if observer is None:
        return False

    try:
        FreeCAD.removeDocumentObserver(
            observer
        )
    except Exception:
        return False

    _OBSERVER = None

    return True
