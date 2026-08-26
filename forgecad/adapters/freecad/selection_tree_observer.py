"""Keep FreeCAD's project tree expanded to the selected ForgeCAD object."""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui


_observer = None


def _display_text(index):
    """Return display text for a model index without assuming one Qt binding."""

    try:
        value = index.data(
            QtCore.Qt.DisplayRole
        )
    except Exception:
        try:
            value = index.data()
        except Exception:
            return ""

    try:
        return str(
            value
        )
    except Exception:
        return ""


def _object_labels(obj):
    """Return user-facing and internal names that may appear in the tree."""

    values = []

    for attribute_name in (
        "Label",
        "Name",
    ):
        value = str(
            getattr(
                obj,
                attribute_name,
                "",
            )
        ).strip()

        if (
            value
            and value not in values
        ):
            values.append(
                value
            )

    return tuple(
        values
    )


def _model_indexes(
    model,
    parent=None,
):
    """Yield every index in a Qt item model depth-first."""

    if model is None:
        return

    if parent is None:
        parent = QtCore.QModelIndex()

    try:
        row_count = model.rowCount(
            parent
        )
    except Exception:
        return

    for row in range(
        int(
            row_count
        )
    ):
        try:
            index = model.index(
                row,
                0,
                parent,
            )
        except Exception:
            continue

        if not index.isValid():
            continue

        yield index

        yield from _model_indexes(
            model,
            index,
        )


def _matching_index(
    tree,
    obj,
):
    """Return the best tree index matching a FreeCAD document object."""

    if (
        tree is None
        or obj is None
    ):
        return None

    try:
        model = tree.model()
    except Exception:
        return None

    labels = _object_labels(
        obj
    )

    if not labels:
        return None

    exact_matches = []

    for index in _model_indexes(
        model
    ):
        text = _display_text(
            index
        ).strip()

        if text in labels:
            exact_matches.append(
                index
            )

    if not exact_matches:
        return None

    # Prefer the visible Label over the internal Name when both appear.
    preferred_label = str(
        getattr(
            obj,
            "Label",
            "",
        )
    ).strip()

    if preferred_label:
        for index in exact_matches:
            if (
                _display_text(
                    index
                ).strip()
                == preferred_label
            ):
                return index

    return exact_matches[
        0
    ]


def _expand_parent_chain(
    tree,
    index,
):
    """Expand every parent needed to reveal one model index."""

    if (
        tree is None
        or index is None
    ):
        return

    parents = []

    try:
        parent = index.parent()
    except Exception:
        return

    while (
        parent is not None
        and parent.isValid()
    ):
        parents.append(
            parent
        )

        parent = parent.parent()

    for parent_index in reversed(
        parents
    ):
        try:
            tree.expand(
                parent_index
            )
        except Exception:
            pass


def candidate_tree_views():
    """Return likely document-tree views from FreeCAD's main window."""

    try:
        main_window = (
            FreeCADGui.getMainWindow()
        )
    except Exception:
        return ()

    if main_window is None:
        return ()

    try:
        views = list(
            main_window.findChildren(
                QtGui.QTreeView
            )
        )
    except Exception:
        return ()

    def priority(
        tree,
    ):
        try:
            name = str(
                tree.objectName()
            ).lower()
        except Exception:
            name = ""

        if "tree" in name:
            return 0

        return 1

    views.sort(
        key=priority
    )

    return tuple(
        views
    )


def reveal_object_in_tree(
    document_name,
    object_name,
):
    """Expand and scroll the project tree to one selected document object."""

    try:
        document = FreeCAD.getDocument(
            str(
                document_name
            )
        )
    except Exception:
        document = None

    if document is None:
        return False

    try:
        obj = document.getObject(
            str(
                object_name
            )
        )
    except Exception:
        obj = None

    if obj is None:
        return False

    for tree in candidate_tree_views():
        index = _matching_index(
            tree,
            obj,
        )

        if index is None:
            continue

        _expand_parent_chain(
            tree,
            index,
        )

        try:
            tree.scrollTo(
                index,
                QtGui.QAbstractItemView.PositionAtCenter,
            )
        except Exception:
            try:
                tree.scrollTo(
                    index
                )
            except Exception:
                pass

        return True

    return False


def schedule_reveal(
    document_name,
    object_name,
):
    """Reveal a selected object after FreeCAD finishes its selection update."""

    def reveal():
        reveal_object_in_tree(
            document_name,
            object_name,
        )

    try:
        QtCore.QTimer.singleShot(
            0,
            reveal,
        )
    except Exception:
        reveal()


class ForgeCADSelectionTreeObserver:
    """Reveal selected document objects in FreeCAD's project tree."""

    def addSelection(
        self,
        document_name,
        object_name,
        sub_name="",
        point=None,
    ):
        schedule_reveal(
            document_name,
            object_name,
        )

    def setSelection(
        self,
        document_name,
    ):
        return None

    def removeSelection(
        self,
        document_name,
        object_name,
        sub_name="",
    ):
        return None

    def clearSelection(
        self,
        document_name="",
    ):
        return None


def register_selection_tree_observer():
    """Register one persistent ForgeCAD selection/tree synchronization observer."""

    global _observer

    if _observer is not None:
        return _observer

    observer = (
        ForgeCADSelectionTreeObserver()
    )

    FreeCADGui.Selection.addObserver(
        observer
    )

    _observer = observer

    return observer


def unregister_selection_tree_observer():
    """Remove the ForgeCAD selection/tree observer when registered."""

    global _observer

    if _observer is None:
        return False

    try:
        FreeCADGui.Selection.removeObserver(
            _observer
        )
    except Exception:
        pass

    _observer = None

    return True


__all__ = [
    "ForgeCADSelectionTreeObserver",
    "candidate_tree_views",
    "register_selection_tree_observer",
    "reveal_object_in_tree",
    "schedule_reveal",
    "unregister_selection_tree_observer",
]
