"""Source-level coverage for bent-source -> bent-target Trim / Extend."""

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


def test_bent_to_bent_target_selection_commits_directly():
    source = method_source(
        "target_selected"
    )

    assert "defer_call" in source
    assert "self.commit" in source
    assert "awaiting_bent_target_endpoint" not in source



def test_bent_to_bent_adapter_chooses_endpoints_automatically():
    source = function_source(
        ADAPTER,
        "_bent_source_automatic_intersection",
    )

    assert "source_endpoints" in source
    assert "target_endpoints" in source
    assert "bent_to_bent_endpoint_intersection_3d" in source



def test_adapter_dispatches_bent_to_bent_helper():
    source = function_source(
        ADAPTER,
        "_trim_extend_bent_member_object",
    )

    assert "bent_to_bent_endpoint_intersection_3d" in source
    assert "target_endpoint" in source
