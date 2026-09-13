"""Source-level regression checks for bent miter continuity."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BENT_OBJECT = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "bent_tube_object.py"
)

MITER_COMMAND = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "commands"
    / "miter_selected.py"
)

FAB_REFRESH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "fabrication_refresh.py"
)


def test_bent_proxy_applies_saved_miter_before_assigning_shape():
    source = BENT_OBJECT.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    apply_index = source.index(
        "apply_bent_miter_shape"
    )

    shape_index = source.index(
        "obj.Shape = shape",
        apply_index,
    )

    assert apply_index < shape_index


def test_miter_selected_refreshes_existing_bent_objects_after_regeneration():
    source = MITER_COMMAND.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    assert (
        "fabrication_layout_id_at_point"
        in source
    )

    regenerate_index = source.index(
        "regenerate_frame("
    )

    refresh_index = source.index(
        "refresh_fabrication_for_document(",
        regenerate_index,
    )

    assert (
        refresh_index
        > regenerate_index
    )


def test_fabrication_refresh_supplies_bent_endpoint_identity_tuple():
    source = FAB_REFRESH.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    assert (
        "fabrication_endpoint_ids"
        in source
    )
