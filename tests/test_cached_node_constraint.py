"""Tests for cached node movement constraints."""

import importlib
import sys
import types


class FakeVector:
    def __init__(
        self,
        x=0.0,
        y=0.0,
        z=0.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class FakePlacement:
    def __init__(
        self,
        point,
    ):
        self.Base = FakeVector(
            *point
        )


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.Vector = FakeVector
sys.modules["FreeCAD"] = fake_freecad

fake_part = types.ModuleType(
    "Part"
)
sys.modules["Part"] = fake_part

node_object = importlib.import_module(
    "forgecad.adapters.freecad.node_object"
)
node_object.FreeCAD.Vector = FakeVector


class FakeDocument:
    pass


class FakeNode:
    def __init__(
        self,
        point=(0.0, 0.0, 0.0),
    ):
        self.Position = FakeVector(
            *point
        )
        self.Placement = FakePlacement(
            point
        )
        self.X = float(point[0])
        self.Y = float(point[1])
        self.Z = float(point[2])
        self.Document = FakeDocument()
        self.Proxy = None


def point_tuple(
    point,
):
    return (
        float(point.x),
        float(point.y),
        float(point.z),
    )


def test_proxy_loads_persisted_constraint_once_at_initialization():
    node = FakeNode()

    persisted = object()
    calls = []

    original_loader = (
        node_object.load_persisted_node_constraint
    )

    node_object.load_persisted_node_constraint = (
        lambda document,
        current_node: (
            calls.append(
                (
                    document,
                    current_node,
                )
            )
            or persisted
        )
    )

    try:
        proxy = node_object.ForgeCADNodeProxy(
            node
        )
    finally:
        node_object.load_persisted_node_constraint = (
            original_loader
        )

    assert calls == [
        (
            node.Document,
            node,
        )
    ]

    assert proxy._movement_constraint is persisted


def test_first_inferred_constraint_is_cached_for_later_drags():
    node = FakeNode()

    proxy = object.__new__(
        node_object.ForgeCADNodeProxy
    )
    proxy._ready = True
    proxy._updating = False
    proxy._last_position = (
        0.0,
        0.0,
        0.0,
    )
    proxy._movement_constraint = None

    inferred = object()
    events = []

    original_infer = (
        node_object.infer_node_constraint
    )
    original_solve = (
        node_object.solve_constrained_node_position
    )
    original_layout = (
        node_object.sync_layout_points_for_node
    )
    original_touch = (
        node_object.touch_connected_members
    )

    node_object.infer_node_constraint = (
        lambda document,
        current_node: (
            events.append(
                "infer"
            )
            or inferred
        )
    )

    node_object.solve_constrained_node_position = (
        lambda document,
        current_node,
        proposed_position,
        constraint=None: (
            events.append(
                (
                    "solve",
                    constraint,
                )
            )
            or FakeVector(
                proposed_position.x,
                0.0,
                proposed_position.z,
            )
        )
    )

    node_object.sync_layout_points_for_node = (
        lambda *args: 0
    )
    node_object.touch_connected_members = (
        lambda *args: ()
    )

    try:
        node.Placement.Base = FakeVector(
            100.0,
            50.0,
            0.0,
        )
        proxy.onChanged(
            node,
            "Placement",
        )

        node.Placement.Base = FakeVector(
            200.0,
            75.0,
            0.0,
        )
        proxy.onChanged(
            node,
            "Placement",
        )

    finally:
        node_object.infer_node_constraint = (
            original_infer
        )
        node_object.solve_constrained_node_position = (
            original_solve
        )
        node_object.sync_layout_points_for_node = (
            original_layout
        )
        node_object.touch_connected_members = (
            original_touch
        )

    assert events == [
        "infer",
        (
            "solve",
            inferred,
        ),
        (
            "solve",
            inferred,
        ),
    ]

    assert proxy._movement_constraint is inferred
    assert point_tuple(
        node.Position
    ) == (
        200.0,
        0.0,
        0.0,
    )


def test_solver_with_cached_constraint_does_not_infer_again():
    document = FakeDocument()
    node = FakeNode()
    cached = object()

    original_infer = (
        node_object.infer_node_constraint
    )

    node_object.infer_node_constraint = (
        lambda document,
        current_node: (
            (_ for _ in ()).throw(
                AssertionError(
                    "Topology inference should not run."
                )
            )
        )
    )

    fake_services = sys.modules.get(
        "forgecad.services.joint_constraints"
    )

    module = types.ModuleType(
        "forgecad.services.joint_constraints"
    )

    module.solve_collinear_through_joint = (
        lambda proposed_position,
        constraint: types.SimpleNamespace(
            x=10.0,
            y=0.0,
            z=0.0,
        )
    )

    sys.modules[
        "forgecad.services.joint_constraints"
    ] = module

    fake_point = sys.modules.get(
        "forgecad.geometry.point"
    )

    point_module = types.ModuleType(
        "forgecad.geometry.point"
    )
    point_module.Point3D = (
        lambda x, y, z: types.SimpleNamespace(
            x=float(x),
            y=float(y),
            z=float(z),
        )
    )
    sys.modules[
        "forgecad.geometry.point"
    ] = point_module

    try:
        solved = node_object.solve_constrained_node_position(
            document,
            node,
            FakeVector(
                10.0,
                20.0,
                0.0,
            ),
            constraint=cached,
        )
    finally:
        node_object.infer_node_constraint = (
            original_infer
        )

        if fake_services is None:
            sys.modules.pop(
                "forgecad.services.joint_constraints",
                None,
            )
        else:
            sys.modules[
                "forgecad.services.joint_constraints"
            ] = fake_services

        if fake_point is None:
            sys.modules.pop(
                "forgecad.geometry.point",
                None,
            )
        else:
            sys.modules[
                "forgecad.geometry.point"
            ] = fake_point

    assert point_tuple(
        solved
    ) == (
        10.0,
        0.0,
        0.0,
    )
