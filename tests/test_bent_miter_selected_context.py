"""Source checks for bent-aware Miter Selected behavior."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "forgecad/adapters/freecad/commands/miter_selected.py"


def function_source(name):
    source = PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        item for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == name
    )
    return ast.get_source_segment(source, node)


def test_preflight_uses_explicit_selection_not_global_joint_lookup():
    source = function_source("_preflight")
    assert "structural_member_from_freecad_object" in source
    assert "joint_from_node_object" not in source
    assert "selection" in source


def test_bent_selection_refreshes_without_layout_regeneration():
    source = function_source("apply_selected_miter")
    assert "has_bent_member" in source
    assert "if has_bent_member" in source
    assert "refresh_fabrication_for_document" in source


def test_straight_selection_keeps_regeneration_path():
    assert "regenerate_frame" in function_source("apply_selected_miter")
