"""Regression tests for finite secondary cope cutters at compound corners."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "forgecad/adapters/freecad/member_notch.py"


def _function_source(name):
    text = PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    matches = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(matches) == 1
    lines = text.splitlines()
    node = matches[0]
    return "\n".join(lines[node.lineno - 1:node.end_lineno])


def test_secondary_cutter_is_explicitly_bounded():
    source = _function_source("apply_bounded_cope_to_existing_shape")
    assert "extension=0.0" in source
    assert "build_through_tube_cutting_tool" in source


def test_primary_cope_still_uses_normal_extended_cutter():
    source = _function_source("apply_cope_to_existing_shape")
    assert "build_through_tube_cutting_tool" in source
    assert "extension=0.0" not in source


def test_secondary_slots_use_bounded_path_and_target_links():
    source = _function_source("build_member_shape")
    assert "StartCope2TargetMember" in source
    assert "EndCope2TargetMember" in source
    assert source.count("apply_bounded_cope_to_existing_shape(") == 4

def test_secondary_does_not_fall_back_to_extended_path():
    source = _function_source("build_member_shape")
    start_block = source[source.index("if bool(obj.StartCope2Enabled):"):source.index("if bool(\n            obj.EndCopeEnabled", source.index("if bool(obj.StartCope2Enabled):"))]
    assert "apply_cope_to_existing_shape(" not in start_block
    assert "apply_bounded_cope_to_existing_shape(" in start_block
