"""Source regression tests for bent-member Clear Selected adapter behavior."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "commands"
    / "clear_selected_joint.py"
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


def test_joint_member_ids_uses_endpoint_aware_fabrication_identity():
    source = _function_source(
        "_joint_member_ids"
    )

    assert (
        "fabrication_layout_id_at_point"
        in source
    )


def test_joint_member_ids_retains_straight_interior_through_support():
    source = _function_source(
        "_joint_member_ids"
    )

    assert (
        "point_on_segment"
        in source
    )


def test_bent_clear_refreshes_in_place_instead_of_regenerating():
    source = _function_source(
        "apply_clear_selected_joint"
    )

    assert (
        "has_bent_member"
        in source
    )

    assert (
        "refresh_fabrication_for_document"
        in source
    )

    assert (
        "regenerate_frame"
        in source
    )


def test_clear_still_preserves_compound_cope_and_through_persistence_paths():
    source = _function_source(
        "apply_clear_selected_joint"
    )

    assert (
        "replace_joint_cope_pairs"
        in source
    )

    assert (
        "replace_joint_through_pairs"
        in source
    )
