"""Tests for FreeCAD node collinear-through movement constraints."""

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

sys.modules[
    "FreeCAD"
] = fake_freecad


fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


import forgecad.adapters.freecad.node_object as node_object


node_object.FreeCAD.Vector = FakeVector


class FakeDocument:
    pass


class FakeNodeObject:
    def __init__(
        self,
        point,
    ):
        self.Position = FakeVector(
            *point
        )

        self.Placement = FakePlacement(
            point
        )

        self.X = float(
            point[0]
        )

        self.Y = float(
            point[1]
        )

        self.Z = float(
            point[2]
        )

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


def test_node_drag_uses_solved_position_before_layout_and_member_refresh():
    node = FakeNodeObject(
        (
            0.0,
            0.0,
            0.0,
        )
    )

    proxy = node_object.ForgeCADNodeProxy(
        node
    )

    node.Placement.Base = FakeVector(
        250.0,
        150.0,
        0.0,
    )

    events = []

    original_solver = (
        node_object.solve_constrained_node_position
    )

    original_layout_sync = (
        node_object.sync_layout_points_for_node
    )

    original_refresh = (
        node_object.refresh_connected_members
    )

    node_object.solve_constrained_node_position = (
        lambda document,
        node_object_value,
        proposed_position,
        constraint=None: (
            events.append(
                (
                    "solve",
                    point_tuple(
                        proposed_position
                    ),
                )
            )
            or FakeVector(
                250.0,
                0.0,
                0.0,
            )
        )
    )

    node_object.sync_layout_points_for_node = (
        lambda document,
        old_position,
        new_position,
        **kwargs: events.append(
            (
                "layout",
                point_tuple(
                    old_position
                ),
                point_tuple(
                    new_position
                ),
            )
        )
        or 0
    )

    node_object.refresh_connected_members = (
        lambda document,
        node_object_value: events.append(
            (
                "refresh",
                point_tuple(
                    node_object_value.Position
                ),
            )
        )
        or ()
    )

    try:
        proxy.onChanged(
            node,
            "Placement",
        )

    finally:
        node_object.solve_constrained_node_position = (
            original_solver
        )

        node_object.sync_layout_points_for_node = (
            original_layout_sync
        )

        node_object.refresh_connected_members = (
            original_refresh
        )

    assert events == [
        (
            "solve",
            (
                250.0,
                150.0,
                0.0,
            ),
        ),
        (
            "layout",
            (
                0.0,
                0.0,
                0.0,
            ),
            (
                250.0,
                0.0,
                0.0,
            ),
        ),
        (
            "refresh",
            (
                250.0,
                0.0,
                0.0,
            ),
        ),
    ]

    assert point_tuple(
        node.Position
    ) == (
        250.0,
        0.0,
        0.0,
    )

    assert point_tuple(
        node.Placement.Base
    ) == (
        250.0,
        0.0,
        0.0,
    )

    assert (
        node.X,
        node.Y,
        node.Z,
    ) == (
        250.0,
        0.0,
        0.0,
    )


def test_node_drag_without_constraint_keeps_proposed_position():
    node = FakeNodeObject(
        (
            0.0,
            0.0,
            0.0,
        )
    )

    proxy = node_object.ForgeCADNodeProxy(
        node
    )

    node.Placement.Base = FakeVector(
        10.0,
        20.0,
        30.0,
    )

    original_solver = (
        node_object.solve_constrained_node_position
    )

    original_layout_sync = (
        node_object.sync_layout_points_for_node
    )

    original_refresh = (
        node_object.refresh_connected_members
    )

    node_object.solve_constrained_node_position = (
        lambda document,
        node_object_value,
        proposed_position,
        constraint=None: FakeVector(
            proposed_position.x,
            proposed_position.y,
            proposed_position.z,
        )
    )

    node_object.sync_layout_points_for_node = (
        lambda document,
        old_position,
        new_position,
        **kwargs: 0
    )

    node_object.refresh_connected_members = (
        lambda document,
        node_object_value: ()
    )

    try:
        proxy.onChanged(
            node,
            "Placement",
        )

    finally:
        node_object.solve_constrained_node_position = (
            original_solver
        )

        node_object.sync_layout_points_for_node = (
            original_layout_sync
        )

        node_object.refresh_connected_members = (
            original_refresh
        )

    assert point_tuple(
        node.Position
    ) == (
        10.0,
        20.0,
        30.0,
    )

    assert point_tuple(
        node.Placement.Base
    ) == (
        10.0,
        20.0,
        30.0,
    )


def test_solver_failure_falls_back_to_proposed_position():
    proposed = FakeVector(
        5.0,
        6.0,
        7.0,
    )

    # A minimal document/node pair intentionally cannot be converted into
    # a ForgeCAD domain joint. The adapter must fail open for editing.
    solved = (
        node_object.solve_constrained_node_position(
            FakeDocument(),
            object(),
            proposed,
        )
    )

    assert point_tuple(
        solved
    ) == (
        5.0,
        6.0,
        7.0,
    )
