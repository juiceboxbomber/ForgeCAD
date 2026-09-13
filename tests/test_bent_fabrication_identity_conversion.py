"""Regression checks for bend-conversion fabrication identity."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "commands"
    / "convert_joint_to_bend.py"
)


def _source():
    return PATH.read_text(
        encoding="utf-8"
    )


def _function_source(
    name,
):
    source = _source()
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


def test_converter_defines_endpoint_identity_properties():
    source = _source()

    assert (
        "StartFabricationLayoutID"
        in source
    )
    assert (
        "EndFabricationLayoutID"
        in source
    )


def test_new_bend_records_both_consumed_layout_ids():
    source = _function_source(
        "create_bent_tube_from_joint"
    )

    assert (
        "set_bent_fabrication_endpoint_ids"
        in source
    )
    assert (
        "member_objects[0]"
        in source
    )
    assert (
        "member_objects[1]"
        in source
    )


def test_append_extension_moves_only_end_identity():
    source = _function_source(
        "extend_existing_bent_object"
    )

    assert (
        "end_layout_id=layout_id"
        in source
    )


def test_prepend_extension_moves_only_start_identity_when_supported():
    source = _source()

    if (
        "def prepend_existing_bent_object("
        not in source
    ):
        return

    prepend = _function_source(
        "prepend_existing_bent_object"
    )

    assert (
        "start_layout_id=layout_id"
        in prepend
    )


def test_converter_still_parses_after_identity_patch():
    ast.parse(
        _source()
    )
