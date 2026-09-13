"""Regression tests for Miter Selected with converted bent members."""

from types import SimpleNamespace

from forgecad.services.selected_miter import (
    selected_miter_request,
)


def _point(
    x,
    y,
    z=0.0,
):
    return SimpleNamespace(
        x=x,
        y=y,
        z=z,
    )


def _node(
    x,
    y,
    z=0.0,
):
    return SimpleNamespace(
        Position=_point(
            x,
            y,
            z,
        )
    )


def test_bent_end_can_be_mitered_to_straight_member():
    bent = SimpleNamespace(
        StartNode=_node(
            0.0,
            0.0,
        ),
        EndNode=_node(
            1000.0,
            1000.0,
        ),
        StartFabricationLayoutID=(
            "L-BEND-START"
        ),
        EndFabricationLayoutID=(
            "L-BEND-END"
        ),
        SourceLayoutLines=(),
    )

    straight = SimpleNamespace(
        SourceLayoutID="L-STRAIGHT",
        StartPoint=_point(
            1000.0,
            1000.0,
        ),
        EndPoint=_point(
            2000.0,
            1000.0,
        ),
    )

    node_xyz, member_ids = (
        selected_miter_request(
            [
                bent,
                straight,
            ]
        )
    )

    assert node_xyz == (
        1000.0,
        1000.0,
        0.0,
    )

    assert member_ids == (
        "L-BEND-END",
        "L-STRAIGHT",
    )


def test_bent_start_uses_start_identity():
    bent = SimpleNamespace(
        StartNode=_node(
            0.0,
            0.0,
        ),
        EndNode=_node(
            1000.0,
            1000.0,
        ),
        StartFabricationLayoutID=(
            "L-BEND-START"
        ),
        EndFabricationLayoutID=(
            "L-BEND-END"
        ),
        SourceLayoutLines=(),
    )

    straight = SimpleNamespace(
        SourceLayoutID="L-STRAIGHT",
        StartPoint=_point(
            0.0,
            0.0,
        ),
        EndPoint=_point(
            -1000.0,
            0.0,
        ),
    )

    _node_xyz, member_ids = (
        selected_miter_request(
            [
                bent,
                straight,
            ]
        )
    )

    assert member_ids[0] == (
        "L-BEND-START"
    )
