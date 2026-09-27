"""Regression tests for Through Selected extension plumbing."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RENDERER = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "renderer.py"
)


def function_source(
    name,
):
    text = RENDERER.read_text(
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


def test_frame_extensions_include_dedicated_through_selected_extensions():
    source = function_source(
        "extension_specifications_for_frame"
    )

    assert (
        "explicit_through_extension_specifications_for_joint"
        in source
    )


def test_frame_extensions_still_include_bent_cope_target_extensions():
    source = function_source(
        "extension_specifications_for_frame"
    )

    assert (
        "explicit_bent_target_extension_specifications_for_joint"
        in source
    )


def test_through_extension_helper_uses_member_through_extension_rules():
    source = function_source(
        "explicit_through_extension_specifications_for_joint"
    )

    assert (
        "member_through_extensions"
        in source
    )

    assert (
        "JointTreatment.member_through"
        in source
    )
