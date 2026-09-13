"""Regression tests for post-regeneration mixed straight/bent fabrication refresh."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "commands"
    / "generate_from_selection.py"
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
        for item in tree.body
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


def test_regenerate_refreshes_combined_fabrication_after_frame_replacement():
    source = _function_source(
        "regenerate_frame"
    )

    assert (
        "refresh_fabrication_for_document"
        in source
    )

    add_index = source.index(
        '.addObject('
    )

    refresh_index = source.index(
        "refresh_fabrication_for_document("
    )

    assert (
        refresh_index
        > add_index
    )


def test_regenerate_refreshes_before_final_topology_or_status_refresh():
    source = _function_source(
        "regenerate_frame"
    )

    refresh_index = source.index(
        "refresh_fabrication_for_document("
    )

    possible_followups = [
        index
        for token in (
            "refresh_joint_topology(",
            "rebuild_joint_status_objects(",
        )
        if (
            index := source.find(
                token
            )
        ) >= 0
    ]

    if possible_followups:
        assert (
            refresh_index
            < min(
                possible_followups
            )
        )


def test_refresh_import_is_local_to_regenerate_to_avoid_adapter_cycles():
    source = _function_source(
        "regenerate_frame"
    )

    assert (
        "from forgecad.adapters.freecad.fabrication_refresh import ("
        in source
    )
