"""Tests for ForgeCAD Generate Nodes command helpers."""

import sys
import types


# ---------------------------------------------------------
# FreeCAD stubs
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.ActiveDocument = None

sys.modules[
    "FreeCAD"
] = fake_freecad


# ---------------------------------------------------------
# Part stub
# ---------------------------------------------------------

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


# ---------------------------------------------------------
# FreeCADGui stubs
# ---------------------------------------------------------

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)

fake_freecad_gui.getMainWindow = (
    lambda: None
)

sys.modules[
    "FreeCADGui"
] = fake_freecad_gui


# ---------------------------------------------------------
# PySide stubs
# ---------------------------------------------------------

fake_pyside = types.ModuleType(
    "PySide"
)

fake_qtgui = types.ModuleType(
    "QtGui"
)


class FakeDialog:
    pass


fake_qtgui.QDialog = (
    FakeDialog
)

fake_pyside.QtGui = (
    fake_qtgui
)

sys.modules[
    "PySide"
] = fake_pyside

sys.modules[
    "PySide.QtGui"
] = fake_qtgui


# ---------------------------------------------------------
# Import module under test
# ---------------------------------------------------------

sys.modules.pop(
    "forgecad.adapters.freecad.commands.generate_nodes",
    None,
)

from forgecad.adapters.freecad.commands.generate_nodes import (
    SOURCE_LAYOUT,
    SOURCE_MANUAL,
    migrate_existing_node_sources,
    next_node_id,
    node_by_point,
    point_key,
    unique_layout_points,
)


# ---------------------------------------------------------
# Fake objects
# ---------------------------------------------------------

class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class FakeLayoutObject:
    def __init__(
        self,
        start,
        end,
    ):
        self.StartPoint = FakeVector(
            *start
        )

        self.EndPoint = FakeVector(
            *end
        )


class FakeNodeObject:
    def __init__(
        self,
        node_id,
        position,
        source_type=None,
    ):
        self.NodeID = node_id
        self.Position = FakeVector(
            *position
        )

        if source_type is not None:
            self.SourceType = (
                source_type
            )

        self._properties = []

    def addProperty(
        self,
        property_type,
        property_name,
        group_name,
    ):
        self._properties.append(
            (
                property_type,
                property_name,
                group_name,
            )
        )

        setattr(
            self,
            property_name,
            "",
        )

    def setEditorMode(
        self,
        property_name,
        mode,
    ):
        pass


class FakeUnrelatedObject:
    pass


class FakeNodesGroup:
    def __init__(
        self,
        objects=None,
    ):
        self.Group = list(
            objects or []
        )


def coordinates(
    points,
):
    """Return XYZ tuples for easier assertions."""

    return [
        (
            point.x,
            point.y,
            point.z,
        )
        for point in points
    ]


# ---------------------------------------------------------
# Point identity
# ---------------------------------------------------------

def test_point_key_returns_coordinate_tuple():
    point = FakeVector(
        100.0,
        250.0,
        50.0,
    )

    assert point_key(
        point
    ) == (
        100.0,
        250.0,
        50.0,
    )


def test_point_key_rounds_coordinates():
    point = FakeVector(
        1.123456789,
        2.987654321,
        3.111111111,
    )

    assert point_key(
        point
    ) == (
        1.123457,
        2.987654,
        3.111111,
    )


# ---------------------------------------------------------
# Unique layout endpoints
# ---------------------------------------------------------

def test_single_layout_line_creates_two_unique_points():
    layout = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    result = unique_layout_points(
        [layout]
    )

    assert coordinates(
        result
    ) == [
        (0.0, 0.0, 0.0),
        (1000.0, 0.0, 0.0),
    ]


def test_connected_lines_share_one_node():
    line_1 = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    line_2 = FakeLayoutObject(
        (1000, 0, 0),
        (1000, 500, 0),
    )

    result = unique_layout_points(
        [
            line_1,
            line_2,
        ]
    )

    assert coordinates(
        result
    ) == [
        (0.0, 0.0, 0.0),
        (1000.0, 0.0, 0.0),
        (1000.0, 500.0, 0.0),
    ]


def test_rectangle_creates_four_unique_nodes():
    objects = [
        FakeLayoutObject(
            (0, 0, 0),
            (1000, 0, 0),
        ),
        FakeLayoutObject(
            (1000, 0, 0),
            (1000, 500, 0),
        ),
        FakeLayoutObject(
            (1000, 500, 0),
            (0, 500, 0),
        ),
        FakeLayoutObject(
            (0, 500, 0),
            (0, 0, 0),
        ),
    ]

    result = unique_layout_points(
        objects
    )

    assert len(
        result
    ) == 4


def test_duplicate_lines_do_not_duplicate_nodes():
    line_1 = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    line_2 = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    result = unique_layout_points(
        [
            line_1,
            line_2,
        ]
    )

    assert len(
        result
    ) == 2


def test_reversed_duplicate_line_does_not_duplicate_nodes():
    line_1 = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    line_2 = FakeLayoutObject(
        (1000, 0, 0),
        (0, 0, 0),
    )

    result = unique_layout_points(
        [
            line_1,
            line_2,
        ]
    )

    assert len(
        result
    ) == 2


def test_unrelated_objects_are_ignored():
    line = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    result = unique_layout_points(
        [
            FakeUnrelatedObject(),
            line,
        ]
    )

    assert coordinates(
        result
    ) == [
        (0.0, 0.0, 0.0),
        (1000.0, 0.0, 0.0),
    ]


def test_nearly_identical_coordinates_are_treated_as_same_node():
    line_1 = FakeLayoutObject(
        (0, 0, 0),
        (1000.0000001, 0, 0),
    )

    line_2 = FakeLayoutObject(
        (1000.0000002, 0, 0),
        (1000, 500, 0),
    )

    result = unique_layout_points(
        [
            line_1,
            line_2,
        ]
    )

    assert len(
        result
    ) == 3


# ---------------------------------------------------------
# Existing-node lookup
# ---------------------------------------------------------

def test_node_by_point_returns_existing_node():
    node = FakeNodeObject(
        "N001",
        (100, 200, 300),
        SOURCE_MANUAL,
    )

    group = FakeNodesGroup(
        [node]
    )

    result = node_by_point(
        group,
        FakeVector(
            100,
            200,
            300,
        ),
    )

    assert result is node


def test_node_by_point_returns_none_when_missing():
    node = FakeNodeObject(
        "N001",
        (100, 200, 300),
        SOURCE_MANUAL,
    )

    group = FakeNodesGroup(
        [node]
    )

    result = node_by_point(
        group,
        FakeVector(
            500,
            500,
            500,
        ),
    )

    assert result is None


# ---------------------------------------------------------
# Node numbering
# ---------------------------------------------------------

def test_next_node_id_starts_at_n001():
    group = FakeNodesGroup()

    assert (
        next_node_id(
            group
        )
        == "N001"
    )


def test_next_node_id_uses_highest_existing_number():
    group = FakeNodesGroup(
        [
            FakeNodeObject(
                "N001",
                (0, 0, 0),
            ),
            FakeNodeObject(
                "N005",
                (1, 0, 0),
            ),
            FakeNodeObject(
                "N003",
                (2, 0, 0),
            ),
        ]
    )

    assert (
        next_node_id(
            group
        )
        == "N006"
    )


def test_next_node_id_ignores_invalid_ids():
    group = FakeNodesGroup(
        [
            FakeNodeObject(
                "Node",
                (0, 0, 0),
            ),
            FakeNodeObject(
                "NABC",
                (1, 0, 0),
            ),
            FakeNodeObject(
                "N007",
                (2, 0, 0),
            ),
        ]
    )

    assert (
        next_node_id(
            group
        )
        == "N008"
    )


# ---------------------------------------------------------
# Source migration
# ---------------------------------------------------------

def test_legacy_node_matching_layout_becomes_layout():
    node = FakeNodeObject(
        "N001",
        (0, 0, 0),
    )

    group = FakeNodesGroup(
        [node]
    )

    migrate_existing_node_sources(
        group,
        [
            FakeVector(
                0,
                0,
                0,
            )
        ],
    )

    assert (
        node.SourceType
        == SOURCE_LAYOUT
    )


def test_legacy_node_not_matching_layout_becomes_manual():
    node = FakeNodeObject(
        "N005",
        (0, 0, 1000),
    )

    group = FakeNodesGroup(
        [node]
    )

    migrate_existing_node_sources(
        group,
        [
            FakeVector(
                0,
                0,
                0,
            )
        ],
    )

    assert (
        node.SourceType
        == SOURCE_MANUAL
    )


def test_existing_manual_source_type_is_preserved():
    node = FakeNodeObject(
        "N005",
        (0, 0, 1000),
        SOURCE_MANUAL,
    )

    group = FakeNodesGroup(
        [node]
    )

    migrate_existing_node_sources(
        group,
        [
            FakeVector(
                0,
                0,
                1000,
            )
        ],
    )

    assert (
        node.SourceType
        == SOURCE_MANUAL
    )


def test_existing_layout_source_type_is_preserved():
    node = FakeNodeObject(
        "N001",
        (0, 0, 0),
        SOURCE_LAYOUT,
    )

    group = FakeNodesGroup(
        [node]
    )

    migrate_existing_node_sources(
        group,
        [
            FakeVector(
                0,
                0,
                0,
            )
        ],
    )

    assert (
        node.SourceType
        == SOURCE_LAYOUT
    )


def test_manual_node_at_layout_coordinate_is_not_reclassified():
    node = FakeNodeObject(
        "N010",
        (1000, 500, 750),
        SOURCE_MANUAL,
    )

    group = FakeNodesGroup(
        [node]
    )

    migrate_existing_node_sources(
        group,
        [
            FakeVector(
                1000,
                500,
                750,
            )
        ],
    )

    assert (
        node.SourceType
        == SOURCE_MANUAL
    )

    # ---------------------------------------------------------
# Layout ownership
# ---------------------------------------------------------

def test_layout_objects_for_point_returns_all_connected_lines():
    from forgecad.adapters.freecad.commands.generate_nodes import (
        layout_objects_for_point,
    )

    through_line = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    branch_line = FakeLayoutObject(
        (500, 0, 0),
        (500, 500, 0),
    )

    result = layout_objects_for_point(
        FakeVector(
            500,
            0,
            0,
        ),
        [
            through_line,
            branch_line,
        ],
    )

    assert result == [
        through_line,
        branch_line,
    ]


def test_ensure_source_layout_objects_stores_connected_layout_objects():
    from forgecad.adapters.freecad.commands.generate_nodes import (
        ensure_source_layout_objects,
    )

    node = FakeNodeObject(
        "N001",
        (500, 0, 0),
        SOURCE_LAYOUT,
    )

    through_line = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    branch_line = FakeLayoutObject(
        (500, 0, 0),
        (500, 500, 0),
    )

    result = ensure_source_layout_objects(
        node,
        [
            through_line,
            branch_line,
        ],
    )

    assert result == [
        through_line,
        branch_line,
    ]

    assert node.SourceLayoutLines == [
        through_line,
        branch_line,
    ]

def test_layout_node_source_ownership_can_be_replaced():
    from forgecad.adapters.freecad.commands.generate_nodes import (
        ensure_source_layout_objects,
    )

    node = FakeNodeObject(
        "N001",
        (500, 0, 0),
        SOURCE_LAYOUT,
    )

    old_line = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    new_line = FakeLayoutObject(
        (500, 0, 0),
        (500, 500, 0),
    )

    ensure_source_layout_objects(
        node,
        [old_line],
    )

    ensure_source_layout_objects(
        node,
        [new_line],
    )

    assert node.SourceLayoutLines == [
        new_line,
    ]


def test_generate_nodes_assigns_layout_ownership_to_reused_layout_node(
    monkeypatch,
):
    import forgecad.adapters.freecad.commands.generate_nodes as module

    through_line = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    branch_line = FakeLayoutObject(
        (500, 0, 0),
        (500, 500, 0),
    )

    existing_node = FakeNodeObject(
        "N001",
        (500, 0, 0),
        SOURCE_LAYOUT,
    )

    nodes_group = FakeNodesGroup(
        [existing_node]
    )

    class FakeDocument:
        def recompute(self):
            pass

    document = FakeDocument()

    monkeypatch.setattr(
        module,
        "initialize_project_tree",
        lambda document: {
            "Nodes": nodes_group,
        },
    )

    monkeypatch.setattr(
    module,
    "ensure_node_proxy",
    lambda obj: obj,
    )

    monkeypatch.setattr(
    module,
    "unique_layout_points",
    lambda layout_objects: [
        FakeVector(
            500,
            0,
            0,
        )
    ],
    )

    monkeypatch.setattr(
        module,
        "remove_obsolete_layout_nodes",
        lambda *args, **kwargs: None,
    )

    result = module.generate_nodes_from_layout(
        document,
        [
            through_line,
            branch_line,
        ],
    )

    assert existing_node in result

    assert existing_node.SourceLayoutLines == [
        through_line,
        branch_line,
    ]


def test_generate_nodes_does_not_assign_layout_ownership_to_manual_node(
    monkeypatch,
):
    import forgecad.adapters.freecad.commands.generate_nodes as module

    layout_line = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    manual_node = FakeNodeObject(
        "N001",
        (0, 0, 0),
        SOURCE_MANUAL,
    )

    nodes_group = FakeNodesGroup(
        [manual_node]
    )

    class FakeDocument:
        def recompute(self):
            pass

    document = FakeDocument()

    monkeypatch.setattr(
        module,
        "initialize_project_tree",
        lambda document: {
            "Nodes": nodes_group,
        },
    )

    monkeypatch.setattr(
        module,
        "ensure_node_proxy",
        lambda obj: obj,
    )

    monkeypatch.setattr(
        module,
        "unique_layout_points",
        lambda layout_objects: [
            FakeVector(
                0,
                0,
                0,
            )
        ],
    )

    monkeypatch.setattr(
        module,
        "remove_obsolete_layout_nodes",
        lambda *args, **kwargs: None,
    )

    result = module.generate_nodes_from_layout(
        document,
        [layout_line],
    )

    assert result == [
        manual_node,
    ]

    assert manual_node.SourceType == SOURCE_MANUAL

    assert not hasattr(
        manual_node,
        "SourceLayoutLines",
    )

def test_generate_nodes_adds_ownership_to_legacy_layout_node(
    monkeypatch,
):
    import forgecad.adapters.freecad.commands.generate_nodes as module

    layout_line = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    legacy_node = FakeNodeObject(
        "N001",
        (0, 0, 0),
    )

    nodes_group = FakeNodesGroup(
        [legacy_node]
    )

    class FakeDocument:
        def recompute(self):
            pass

    document = FakeDocument()

    monkeypatch.setattr(
        module,
        "initialize_project_tree",
        lambda document: {
            "Nodes": nodes_group,
        },
    )

    monkeypatch.setattr(
        module,
        "ensure_node_proxy",
        lambda obj: obj,
    )

    monkeypatch.setattr(
        module,
        "unique_layout_points",
        lambda layout_objects: [
            FakeVector(
                0,
                0,
                0,
            )
        ],
    )

    monkeypatch.setattr(
        module,
        "remove_obsolete_layout_nodes",
        lambda *args, **kwargs: None,
    )

    result = module.generate_nodes_from_layout(
        document,
        [layout_line],
    )

    assert result == [
        legacy_node,
    ]

    assert legacy_node.SourceType == SOURCE_LAYOUT

    assert legacy_node.SourceLayoutLines == [
        layout_line,
    ]


def test_generate_nodes_refreshes_layout_ownership_on_regeneration(
    monkeypatch,
):
    import forgecad.adapters.freecad.commands.generate_nodes as module

    through_line = FakeLayoutObject(
        (0, 0, 0),
        (1000, 0, 0),
    )

    branch_line = FakeLayoutObject(
        (500, 0, 0),
        (500, 500, 0),
    )

    node = FakeNodeObject(
        "N001",
        (500, 0, 0),
        SOURCE_LAYOUT,
    )

    nodes_group = FakeNodesGroup(
        [node]
    )

    class FakeDocument:
        def recompute(self):
            pass

    document = FakeDocument()

    monkeypatch.setattr(
        module,
        "initialize_project_tree",
        lambda document: {
            "Nodes": nodes_group,
        },
    )

    monkeypatch.setattr(
        module,
        "ensure_node_proxy",
        lambda obj: obj,
    )

    monkeypatch.setattr(
        module,
        "unique_layout_points",
        lambda layout_objects: [
            FakeVector(
                500,
                0,
                0,
            )
        ],
    )

    monkeypatch.setattr(
        module,
        "remove_obsolete_layout_nodes",
        lambda *args, **kwargs: None,
    )

    module.generate_nodes_from_layout(
        document,
        [
            through_line,
            branch_line,
        ],
    )

    assert node.SourceLayoutLines == [
        through_line,
        branch_line,
    ]

    module.generate_nodes_from_layout(
        document,
        [
            through_line,
        ],
    )

    assert node.SourceLayoutLines == [
        through_line,
    ]
