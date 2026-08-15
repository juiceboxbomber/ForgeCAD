"""Tests for bent-tube endpoint node creation."""

import sys
import types


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(
            x
        )
        self.y = float(
            y
        )
        self.z = float(
            z
        )


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.Vector = FakeVector
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_part = types.ModuleType(
    "Part"
)

fake_pyside = types.ModuleType(
    "PySide"
)


class FakeQDialog:
    Accepted = 1


fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=FakeQDialog,
)


# ---------------------------------------------------------
# Save any modules that were already present.
#
# These tests need fake FreeCAD modules, but they must not
# leak into later test modules.
# ---------------------------------------------------------

_original_modules = {
    name: sys.modules.get(
        name
    )
    for name in (
        "FreeCAD",
        "FreeCADGui",
        "Part",
        "PySide",
    )
}


sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = fake_freecad_gui

sys.modules[
    "Part"
] = fake_part

sys.modules[
    "PySide"
] = fake_pyside


# ---------------------------------------------------------
# Avoid loading the real bent-tube FreeCAD geometry adapter.
#
# The endpoint-node helpers being tested do not need actual
# FreeCAD shape creation.
# ---------------------------------------------------------

fake_bent_tube_object = types.ModuleType(
    "forgecad.adapters.freecad.bent_tube_object"
)


def _unused_create_bent_tube_object(
    *args,
    **kwargs,
):
    raise AssertionError(
        "create_bent_tube_object should not be called "
        "by endpoint-node helper tests."
    )


fake_bent_tube_object.create_bent_tube_object = (
    _unused_create_bent_tube_object
)

sys.modules[
    "forgecad.adapters.freecad.bent_tube_object"
] = (
    fake_bent_tube_object
)


from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)

from forgecad.adapters.freecad.commands import (
    create_bent_tube as command,
)


# ---------------------------------------------------------
# Restore global module state immediately after importing
# the command under test.
#
# The command module keeps the references it needs, while
# later tests are free to install their own FreeCAD stubs.
# ---------------------------------------------------------

for _name, _module in _original_modules.items():
    if _module is None:
        sys.modules.pop(
            _name,
            None,
        )
    else:
        sys.modules[
            _name
        ] = _module


sys.modules.pop(
    "forgecad.adapters.freecad.bent_tube_object",
    None,
)

# Defensive cleanup in case either of these was imported
# indirectly while our temporary fake Part module existed.
sys.modules.pop(
    "forgecad.adapters.freecad.bent_tube_geometry",
    None,
)


class FakeViewObject:
    PointSize = 0.0


class FakeNodeObject:
    def __init__(
        self,
        name,
    ):
        self.Name = name
        self.Label = name
        self.ViewObject = FakeViewObject()

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        setattr(
            self,
            property_name,
            None,
        )

    def setEditorMode(
        self,
        property_name,
        mode,
    ):
        pass


class FakeGroup:
    def __init__(
        self,
        name,
    ):
        self.Name = name
        self.Group = []

    def addObject(
        self,
        obj,
    ):
        if obj not in self.Group:
            self.Group.append(
                obj
            )


class FakeDocument:
    def __init__(
        self,
    ):
        self.objects = {}
        self.recompute_count = 0

    def addObject(
        self,
        type_name,
        name,
    ):
        obj = FakeNodeObject(
            name
        )

        self.objects[
            name
        ] = obj

        return obj

    def getObject(
        self,
        name,
    ):
        return self.objects.get(
            name
        )

    def recompute(
        self,
    ):
        self.recompute_count += 1


def _tube():
    return BentTube(
        straight_runs=(
            StraightRun(
                500.0
            ),
            StraightRun(
                500.0
            ),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
        ),
        profile=TubeProfile(
            outside_diameter=44.45,
            wall_thickness=3.048,
        ),
        material=Material(
            name="A513 Type 5 DOM",
            density=7850.0,
            yield_strength=350.0,
        ),
    )


class FakeBentProxy:
    def _tube_from_properties(
        self,
        obj,
    ):
        return _tube()


class FakeBentObject:
    def __init__(
        self,
    ):
        self.Proxy = FakeBentProxy()

        self.StartPoint = FakeVector(
            0.0,
            0.0,
            0.0,
        )

        self.InitialDirection = FakeVector(
            1.0,
            0.0,
            0.0,
        )

        self.InitialBendNormal = FakeVector(
            0.0,
            0.0,
            1.0,
        )


def _node(
    node_id,
    x,
    y,
    z,
):
    obj = FakeNodeObject(
        "ForgeCADNode"
    )

    obj.NodeID = node_id

    obj.Position = FakeVector(
        x,
        y,
        z,
    )

    obj.SourceType = "Manual"

    return obj


def test_solved_endpoints_use_true_bent_centerline():
    start, end = (
        command.solved_bent_tube_endpoints(
            FakeBentObject()
        )
    )

    assert (
        start.x,
        start.y,
        start.z,
    ) == (
        0.0,
        0.0,
        0.0,
    )

    assert abs(
        end.x - 600.0
    ) < 1e-9

    assert abs(
        end.y - 600.0
    ) < 1e-9

    assert abs(
        end.z
    ) < 1e-9


def test_ensure_node_at_point_reuses_existing_node():
    document = FakeDocument()

    nodes_group = FakeGroup(
        "ForgeCADNodes"
    )

    existing = _node(
        "N001",
        0.0,
        0.0,
        0.0,
    )

    nodes_group.addObject(
        existing
    )

    result = command.ensure_node_at_point(
        document,
        nodes_group,
        FakeVector(
            0.0,
            0.0,
            0.0,
        ),
    )

    assert result is existing

    assert len(
        nodes_group.Group
    ) == 1


def test_ensure_node_at_point_creates_manual_node():
    document = FakeDocument()

    nodes_group = FakeGroup(
        "ForgeCADNodes"
    )

    # create_node_object() uses FreeCAD and Part from the
    # generate_nodes module imported by the command.
    command.create_node_object.__globals__[
        "Part"
    ].makeSphere = (
        lambda radius, point: (
            radius,
            point,
        )
    )

    result = command.ensure_node_at_point(
        document,
        nodes_group,
        FakeVector(
            10.0,
            20.0,
            30.0,
        ),
    )

    assert result.NodeID == "N001"
    assert result.SourceType == "Manual"

    assert (
        result.Position.x,
        result.Position.y,
        result.Position.z,
    ) == (
        10.0,
        20.0,
        30.0,
    )

    assert result in nodes_group.Group


def test_endpoint_node_creation_reuses_start_and_creates_end(
    monkeypatch,
):
    document = FakeDocument()

    nodes_group = FakeGroup(
        "ForgeCADNodes"
    )

    existing_start = _node(
        "N001",
        0.0,
        0.0,
        0.0,
    )

    nodes_group.addObject(
        existing_start
    )

    command.create_node_object.__globals__[
        "Part"
    ].makeSphere = (
        lambda radius, point: (
            radius,
            point,
        )
    )

    monkeypatch.setattr(
        command,
        "initialize_project_tree",
        lambda document: {
            "Nodes": nodes_group,
        },
    )

    start_node, end_node = (
        command.ensure_bent_tube_endpoint_nodes(
            document,
            FakeBentObject(),
        )
    )

    assert start_node is existing_start
    assert end_node.NodeID == "N002"

    assert abs(
        end_node.Position.x - 600.0
    ) < 1e-9

    assert abs(
        end_node.Position.y - 600.0
    ) < 1e-9

    assert abs(
        end_node.Position.z
    ) < 1e-9

    assert len(
        nodes_group.Group
    ) == 2
    