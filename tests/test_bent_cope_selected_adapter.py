"""Source-level guards for bent-aware Cope Selected adapter behavior."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMAND = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "commands"
    / "cope_selected.py"
)


def function_source(name):
    text = COMMAND.read_text(
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


def test_joint_context_resolves_endpoint_fabrication_identity():
    source = function_source(
        "_joint_context"
    )

    assert (
        "fabrication_layout_id_at_point"
        in source
    )


def test_bent_target_path_refreshes_existing_structural_objects_in_place():
    source = function_source(
        "apply_selected_cope"
    )

    assert (
        "has_bent_target"
        in source
    )
    assert (
        "refresh_fabrication_for_document"
        in source
    )
    assert (
        "if has_bent_target"
        in source
    )
