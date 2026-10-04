"""Source-level straight-source -> bent-target Trim / Extend coverage."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "forgecad/adapters/freecad/commands/trim_extend_member.py"
ADAPTER = ROOT / "forgecad/adapters/freecad/member_trim_extend_adapter.py"


def method_source(name):
    text = COMMAND.read_text(encoding="utf-8")
    tree = ast.parse(text)
    cls = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "InteractiveTrimExtendTool"
    )
    node = next(
        node for node in cls.body
        if isinstance(node, ast.FunctionDef)
        and node.name == name
    )
    return ast.get_source_segment(text, node)


def function_source(path, name):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    node = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == name
    )
    return ast.get_source_segment(text, node)


def test_bent_target_commits_without_endpoint_click():
    source = method_source(
        "target_selected"
    )

    assert "defer_call" in source
    assert "self.commit" in source
    assert "add_trim_click_callback" not in source



def test_adapter_chooses_bent_target_endpoint_automatically():
    source = function_source(
        ADAPTER,
        "_straight_to_bent_automatic_intersection",
    )

    assert "straight_to_bent_endpoint_intersection_3d" in source
    assert '"start"' in source
    assert '"end"' in source



def test_commit_passes_target_endpoint():
    source = method_source("commit")
    assert "target_endpoint=" in source


def test_adapter_dispatches_bent_target_helper():
    source = function_source(
        ADAPTER,
        "trim_extend_member_object",
    )
    assert "straight_to_bent_endpoint_intersection_3d" in source
