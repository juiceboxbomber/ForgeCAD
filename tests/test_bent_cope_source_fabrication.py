"""Regression guards for cylindrical copes on bent source members."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BENT_FABRICATION = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "bent_fabrication.py"
)

BENT_OBJECT = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "bent_tube_object.py"
)


def function_source(path, name):
    text = path.read_text(
        encoding="utf-8"
    )
    tree = ast.parse(
        text
    )

    for node in ast.walk(
        tree
    ):
        if (
            isinstance(
                node,
                ast.FunctionDef,
            )
            and node.name == name
        ):
            return ast.get_source_segment(
                text,
                node,
            )

    raise AssertionError(
        f"{name} not found in {path}"
    )


def test_bent_endpoint_cope_uses_temporary_stock_and_bent_specific_boolean():
    source = function_source(
        BENT_FABRICATION,
        "_apply_bent_endpoint_copes",
    )

    assert (
        "temporary_cope_extension"
        in source
    )

    assert (
        "_fuse_endpoint_extension"
        in source
    )

    assert (
        "build_through_tube_cutting_tool"
        in source
    )

    assert (
        "shape.cut("
        in source
    )

    assert (
        "_primary_bent_cope_component"
        in source
    )

    assert (
        "apply_cope_to_existing_shape"
        not in source
    )



def test_bent_fabrication_supports_three_cope_slots_per_end():
    source = function_source(
        BENT_FABRICATION,
        "apply_bent_miter_shape",
    )

    for name in (
        "StartCope",
        "StartCope2",
        "StartCope3",
        "EndCope",
        "EndCope2",
        "EndCope3",
    ):
        assert name in source


def test_bent_cope_precedes_planar_miter():
    source = function_source(
        BENT_FABRICATION,
        "apply_bent_miter_shape",
    )

    assert source.index(
        "_apply_bent_endpoint_copes("
    ) < source.index(
        '"StartMiterEnabled"'
    )


def test_bent_tube_rebuild_refreshes_linked_cope_target_axes():
    source = function_source(
        BENT_OBJECT,
        "update_shape",
    )

    assert source.index(
        "sync_cope_axes_from_target_members"
    ) < source.index(
        "build_bent_tube_shape"
    )
