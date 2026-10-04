"""Unified one-click destination workflow for Trim / Extend."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

COMMAND = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "commands"
    / "trim_extend_member.py"
)

ADAPTER = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "member_trim_extend_adapter.py"
)


def function_source(
    path,
    name,
):
    text = path.read_text(
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


def method_source(
    name,
):
    text = COMMAND.read_text(
        encoding="utf-8"
    )
    tree = ast.parse(
        text
    )
    cls = next(
        item
        for item in tree.body
        if isinstance(
            item,
            ast.ClassDef,
        )
        and item.name == "InteractiveTrimExtendTool"
    )
    node = next(
        item
        for item in cls.body
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


def test_destination_selection_commits_without_extra_endpoint_clicks():
    source = method_source(
        "target_selected"
    )

    assert "defer_call" in source
    assert "self.commit" in source
    assert "add_trim_click_callback" not in source
    assert "awaiting_bent_target_endpoint" not in source


def test_adapter_automatically_chooses_straight_source_endpoint():
    source = function_source(
        ADAPTER,
        "trim_extend_member_object",
    )

    assert "_automatic_straight_endpoint" in source


def test_adapter_automatically_chooses_bent_target_endpoint():
    source = function_source(
        ADAPTER,
        "_straight_to_bent_automatic_intersection",
    )

    assert '"start"' in source
    assert '"end"' in source
    assert "straight_to_bent_endpoint_intersection_3d" in source


def test_bent_source_resolver_checks_both_source_and_target_ends():
    source = function_source(
        ADAPTER,
        "_bent_source_automatic_intersection",
    )

    assert "source_endpoints" in source
    assert "target_endpoints" in source
    assert "bent_to_bent_endpoint_intersection_3d" in source
    assert "bent_endpoint_intersection_3d" in source
