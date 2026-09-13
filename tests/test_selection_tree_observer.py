"""Tests for ForgeCAD selection-to-tree synchronization."""

import importlib
import sys
import types


class FakeQt:
    DisplayRole = 0


class FakeModelIndex:
    def __init__(
        self,
        model=None,
        node=None,
        parent=None,
    ):
        self._model = model
        self.node = node
        self._parent = parent

    def isValid(
        self,
    ):
        return self.node is not None

    def data(
        self,
        role=None,
    ):
        if self.node is None:
            return None

        return self.node[
            "text"
        ]

    def parent(
        self,
    ):
        if self._parent is None:
            return FakeModelIndex()

        return self._parent


class FakeModel:
    def __init__(
        self,
        roots,
    ):
        self.roots = roots

    def _children(
        self,
        parent,
    ):
        if (
            parent is None
            or not parent.isValid()
        ):
            return self.roots

        return parent.node.get(
            "children",
            [],
        )

    def rowCount(
        self,
        parent,
    ):
        return len(
            self._children(
                parent
            )
        )

    def index(
        self,
        row,
        column,
        parent,
    ):
        children = self._children(
            parent
        )

        if (
            row < 0
            or row >= len(
                children
            )
        ):
            return FakeModelIndex()

        return FakeModelIndex(
            self,
            children[
                row
            ],
            parent=(
                parent
                if parent is not None
                and parent.isValid()
                else None
            ),
        )


class FakeTree:
    def __init__(
        self,
        model,
    ):
        self._model = model
        self.expanded = []
        self.scrolled = []

    def model(
        self,
    ):
        return self._model

    def expand(
        self,
        index,
    ):
        self.expanded.append(
            index.data()
        )

    def scrollTo(
        self,
        index,
        *args,
    ):
        self.scrolled.append(
            index.data()
        )

    def objectName(
        self,
    ):
        return "treeView"


class FakeDocument:
    def __init__(
        self,
        obj,
    ):
        self.obj = obj

    def getObject(
        self,
        name,
    ):
        if name == self.obj.Name:
            return self.obj

        return None


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_freecad_gui.Selection = types.SimpleNamespace(
    addObserver=lambda observer: None,
    removeObserver=lambda observer: None,
)

fake_qt_core = types.SimpleNamespace(
    Qt=FakeQt,
    QModelIndex=FakeModelIndex,
    QTimer=types.SimpleNamespace(
        singleShot=lambda delay, callback: callback()
    ),
)

fake_qt_gui = types.SimpleNamespace(
    QTreeView=object,
    QAbstractItemView=types.SimpleNamespace(
        PositionAtCenter=0,
    ),
)

fake_pyside = types.ModuleType(
    "PySide"
)

fake_pyside.QtCore = fake_qt_core
fake_pyside.QtGui = fake_qt_gui

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "FreeCADGui"
] = fake_freecad_gui
sys.modules[
    "PySide"
] = fake_pyside

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


module = importlib.import_module(
    "forgecad.adapters.freecad.selection_tree_observer"
)


def test_reveal_expands_parent_chain_and_scrolls_to_object(
    monkeypatch,
):
    obj = types.SimpleNamespace(
        Name="ForgeCADBentTube",
        Label="Main Hoop",
    )

    roots = [
        {
            "text": "ForgeCAD",
            "children": [
                {
                    "text": "Bent Tubes",
                    "children": [
                        {
                            "text": "Main Hoop",
                            "children": [],
                        },
                    ],
                },
            ],
        },
    ]

    tree = FakeTree(
        FakeModel(
            roots
        )
    )

    fake_freecad.getDocument = (
        lambda name: FakeDocument(
            obj
        )
    )

    monkeypatch.setattr(
        module,
        "candidate_tree_views",
        lambda: (
            tree,
        ),
    )

    result = (
        module.reveal_object_in_tree(
            "Document",
            "ForgeCADBentTube",
        )
    )

    assert result is True

    assert tree.expanded == [
        "ForgeCAD",
        "Bent Tubes",
    ]

    assert tree.scrolled == [
        "Main Hoop",
    ]


def test_selection_observer_schedules_selected_object(
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        module,
        "schedule_reveal",
        lambda document_name, object_name: calls.append(
            (
                document_name,
                object_name,
            )
        ),
    )

    observer = (
        module.ForgeCADSelectionTreeObserver()
    )

    observer.addSelection(
        "Document",
        "ForgeCADNode",
        "",
        None,
    )

    assert calls == [
        (
            "Document",
            "ForgeCADNode",
        ),
    ]


def test_registration_is_idempotent(
    monkeypatch,
):
    added = []

    module._observer = None

    monkeypatch.setattr(
        fake_freecad_gui.Selection,
        "addObserver",
        lambda observer: added.append(
            observer
        ),
    )

    first = (
        module.register_selection_tree_observer()
    )

    second = (
        module.register_selection_tree_observer()
    )

    assert first is second
    assert len(
        added
    ) == 1
