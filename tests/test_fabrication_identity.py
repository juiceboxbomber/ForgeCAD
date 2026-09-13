"""Tests for endpoint-aware ForgeCAD fabrication identity."""

from types import SimpleNamespace

import pytest

from forgecad.services.fabrication_identity import (
    bent_endpoint_layout_ids,
    fabrication_endpoint_ids,
    fabrication_layout_id_at_point,
    structural_endpoint_points,
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


def test_straight_member_uses_one_layout_id_at_both_ends():
    obj = SimpleNamespace(
        SourceLayoutID="L-STRAIGHT",
        StartPoint=_point(
            0.0,
            0.0,
        ),
        EndPoint=_point(
            1000.0,
            0.0,
        ),
    )

    assert (
        fabrication_endpoint_ids(
            obj
        )
        == (
            "L-STRAIGHT",
            "L-STRAIGHT",
        )
    )


def test_bent_member_uses_different_start_and_end_identities():
    obj = SimpleNamespace(
        StartNode=_node(
            0.0,
            0.0,
        ),
        EndNode=_node(
            1000.0,
            1000.0,
        ),
        StartFabricationLayoutID="L-A",
        EndFabricationLayoutID="L-B",
        SourceLayoutLines=(),
    )

    assert (
        fabrication_endpoint_ids(
            obj
        )
        == (
            "L-A",
            "L-B",
        )
    )


def test_legacy_bent_member_falls_back_to_source_layout_order():
    obj = SimpleNamespace(
        StartNode=_node(
            0.0,
            0.0,
        ),
        EndNode=_node(
            1000.0,
            1000.0,
        ),
        SourceLayoutLines=(
            SimpleNamespace(
                LayoutID="L-FIRST"
            ),
            SimpleNamespace(
                LayoutID="L-MIDDLE"
            ),
            SimpleNamespace(
                LayoutID="L-LAST"
            ),
        ),
    )

    assert (
        bent_endpoint_layout_ids(
            obj
        )
        == (
            "L-FIRST",
            "L-LAST",
        )
    )


def test_legacy_lightweight_string_references_are_supported():
    obj = SimpleNamespace(
        SourceLayoutLines=(
            "L-FIRST",
            "L-LAST",
        )
    )

    assert (
        bent_endpoint_layout_ids(
            obj
        )
        == (
            "L-FIRST",
            "L-LAST",
        )
    )


def test_linked_nodes_supply_bent_structural_endpoints():
    start = _node(
        1.0,
        2.0,
        3.0,
    )
    end = _node(
        4.0,
        5.0,
        6.0,
    )

    obj = SimpleNamespace(
        StartNode=start,
        EndNode=end,
    )

    assert (
        structural_endpoint_points(
            obj
        )
        == (
            start.Position,
            end.Position,
        )
    )


def test_endpoint_lookup_selects_correct_bent_identity():
    obj = SimpleNamespace(
        StartNode=_node(
            0.0,
            0.0,
        ),
        EndNode=_node(
            1000.0,
            1000.0,
        ),
        StartFabricationLayoutID="L-START",
        EndFabricationLayoutID="L-END",
        SourceLayoutLines=(),
    )

    assert (
        fabrication_layout_id_at_point(
            obj,
            _point(
                1000.0,
                1000.0,
            ),
        )
        == "L-END"
    )


def test_nonendpoint_lookup_is_rejected():
    obj = SimpleNamespace(
        SourceLayoutID="L1",
        StartPoint=_point(
            0.0,
            0.0,
        ),
        EndPoint=_point(
            1000.0,
            0.0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="not a structural endpoint",
    ):
        fabrication_layout_id_at_point(
            obj,
            _point(
                500.0,
                0.0,
            ),
        )


def test_missing_bent_endpoint_identity_is_rejected():
    obj = SimpleNamespace(
        StartNode=_node(
            0.0,
            0.0,
        ),
        EndNode=_node(
            1000.0,
            1000.0,
        ),
        SourceLayoutLines=(),
    )

    with pytest.raises(
        ValueError,
        match="no fabrication identity",
    ):
        fabrication_layout_id_at_point(
            obj,
            obj.StartNode.Position,
        )
