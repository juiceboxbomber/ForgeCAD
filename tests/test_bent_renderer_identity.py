"""Tests for renderer support of multi-ID bent structural members."""

import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "renderer.py"
)


def _function_source(
    name,
):
    source = PATH.read_text(
        encoding="utf-8"
    )
    tree = ast.parse(
        source
    )

    node = next(
        item
        for item
        in tree.body
        if isinstance(
            item,
            ast.FunctionDef,
        )
        and item.name == name
    )

    return ast.get_source_segment(
        source,
        node,
    )


def _namespace():
    namespace = {}

    exec(
        _function_source(
            "member_layout_id_map"
        ),
        namespace,
    )
    exec(
        _function_source(
            "member_for_layout_id"
        ),
        namespace,
    )

    return namespace


def test_scalar_straight_identity_remains_backward_compatible():
    namespace = _namespace()

    member = object()
    frame = SimpleNamespace(
        members=[
            member
        ]
    )

    result = namespace[
        "member_layout_id_map"
    ](
        frame,
        [
            "L1"
        ],
    )

    assert result[
        id(
            member
        )
    ] == "L1"


def test_bent_member_can_own_two_endpoint_layout_ids():
    namespace = _namespace()

    bent = object()
    other = object()

    frame = SimpleNamespace(
        members=[
            bent,
            other,
        ]
    )

    identities = namespace[
        "member_layout_id_map"
    ](
        frame,
        [
            (
                "L-START",
                "L-END",
            ),
            "L-OTHER",
        ],
    )

    joint = SimpleNamespace(
        members=[
            bent,
            other,
        ]
    )

    assert (
        namespace[
            "member_for_layout_id"
        ](
            joint,
            "L-START",
            identities,
        )
        is bent
    )

    assert (
        namespace[
            "member_for_layout_id"
        ](
            joint,
            "L-END",
            identities,
        )
        is bent
    )
