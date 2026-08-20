"""Post-Undo/Redo refresh support for parametric ForgeCAD objects."""

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
    Touch node-linked straight members and run one normal recompute.

    Shape is never rebuilt directly here. TubeMemberProxy.execute() owns
    synchronization from StartNode/EndNode and rebuilding of member Shape.
    """

    if document is None:
        return ()

    touched = []

    for obj in getattr(
        document,
        "Objects",
        (),
    ):
        if not is_parametric_tube_member(
            obj
        ):
            continue

        try:
            obj.touch()
        except Exception:
            continue

        touched.append(
            obj
        )

    if touched:
        try:
            document.recompute()
        except Exception:
            pass

    return tuple(
        touched
    )


def rebuild_disposable_joint_markers(
    document,
):
    """
    Rebuild ForgeCAD joint-status marker objects from current frame state.

    Joint markers are disposable Part::Feature objects. They are rebuilt
    only after member geometry has finished its normal post-Undo/Redo
    recompute.
    """

    if document is None:
        return ()

    try:
        from forgecad.adapters.freecad.joint_status_objects import (
            rebuild_joint_status_objects,
        )

        return rebuild_joint_status_objects(
            document
        )

    except Exception:
        return ()


def refresh_after_undo_redo(
    document,
):
    """
    Restore parametric members first, then rebuild disposable joint markers.
    """

    touched = refresh_parametric_members(
        document
    )

    markers = rebuild_disposable_joint_markers(
        document
    )

    return (
        touched,
        markers,
    )


class ForgeCADUndoRedoObserver:
    """Refresh ForgeCAD dependencies after FreeCAD Undo or Redo."""

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
