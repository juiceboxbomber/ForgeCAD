"""Bent-to-bent Cope Selected endpoint and recompute regressions."""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from forgecad.services.selected_cope import (
    selected_cope_request,
)


ROOT = Path(__file__).resolve().parents[1]

MEMBER_NOTCH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "member_notch.py"
)


def point(
    x,
    y,
    z=0.0,
):
    return SimpleNamespace(
        x=x,
        y=y,
        z=z,
    )


def node(
    xyz,
):
    return SimpleNamespace(
        Position=point(
            *xyz
        )
    )


def bent(
    start,
    end,
    start_id,
    end_id,
):
    return SimpleNamespace(
        StartNode=node(
            start
        ),
        EndNode=node(
            end
        ),
        StartFabricationLayoutID=start_id,
        EndFabricationLayoutID=end_id,
        SourceLayoutLines=(),
    )


@pytest.mark.parametrize(
    (
        "source_joint",
        "target_joint",
        "expected_source_id",
        "expected_target_id",
    ),
    (
        (
            "start",
            "start",
            "SOURCE-START",
            "TARGET-START",
        ),
        (
            "start",
            "end",
            "SOURCE-START",
            "TARGET-END",
        ),
        (
            "end",
            "start",
            "SOURCE-END",
            "TARGET-START",
        ),
        (
            "end",
            "end",
            "SOURCE-END",
            "TARGET-END",
        ),
    ),
)
def test_bent_to_bent_selection_supports_all_physical_endpoint_pairings(
    source_joint,
    target_joint,
    expected_source_id,
    expected_target_id,
):
    source_start = (
        0.0,
        0.0,
        0.0,
    )
    source_end = (
        600.0,
        600.0,
        0.0,
    )

    joint = (
        source_start
        if source_joint == "start"
        else source_end
    )

    target_other = (
        900.0,
        -300.0,
        0.0,
    )

    if target_joint == "start":
        target_start = joint
        target_end = target_other
    else:
        target_start = target_other
        target_end = joint

    source = bent(
        source_start,
        source_end,
        "SOURCE-START",
        "SOURCE-END",
    )

    target = bent(
        target_start,
        target_end,
        "TARGET-START",
        "TARGET-END",
    )

    (
        node_xyz,
        source_id,
        target_ids,
    ) = selected_cope_request(
        [
            source,
            target,
        ]
    )

    assert node_xyz == joint
    assert source_id == expected_source_id
    assert target_ids == (
        expected_target_id,
    )


def function_source(
    name,
):
    text = MEMBER_NOTCH.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        text
    )

    node = next(
        item
        for item in tree.body
        if isinstance(
            item,
            ast.FunctionDef,
        )
        and item.name == name
    )

    return ast.get_source_segment(
        text,
        node,
    )


def test_link_sync_can_resolve_bent_source_end_without_end_point_property():
    source = function_source(
        "sync_cope_axes_from_target_members"
    )

    assert '"EndNode"' in source
    assert '"StartNode"' in source
    assert '"EndPoint"' in source
    assert "domain_source" in source


def test_link_sync_still_uses_bent_target_terminal_tangent():
    source = function_source(
        "sync_cope_axes_from_target_members"
    )

    assert (
        "member_direction_from_node"
        in source
    )

    assert (
        "domain_target.tube.straight_runs"
        in source
    )

    assert (
        "SourceLayoutID"
        in source
    )
