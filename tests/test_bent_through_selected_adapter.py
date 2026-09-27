"""Source-level regressions for bent-member Through Selected command wiring."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

COMMAND = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "commands"
    / "through_selected.py"
)


def function_source(
    name,
):
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


def test_preflight_resolves_endpoint_specific_fabrication_identity():
    source = function_source(
        "_preflight"
    )

    assert (
        "_fabrication_id_at_joint"
        in source
    )

    assert (
        "{_layout_id(obj): obj"
        not in source
    )


def test_bent_selection_refreshes_existing_fabrication_in_place():
    source = function_source(
        "apply_selected_through"
    )

    assert (
        "_selection_has_bent_member"
        in source
    )

    assert (
        "refresh_fabrication_for_document"
        in source
    )

    assert (
        "if has_bent_member"
        in source
    )


def test_straight_only_selection_keeps_existing_regenerate_path():
    source = function_source(
        "apply_selected_through"
    )

    assert (
        "regenerate_frame"
        in source
    )

    assert (
        "else:"
        in source
    )
