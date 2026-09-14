"""Bent-source cope component retention regressions."""

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


class FakeSolid:
    def __init__(
        self,
        volume,
        name,
    ):
        self.Volume = volume
        self.name = name


class FakeShape:
    def __init__(
        self,
        solids,
    ):
        self.Solids = list(
            solids
        )


def function_source(name):
    text = BENT_FABRICATION.read_text(
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


def loaded_function(name):
    namespace = {}

    exec(
        compile(
            function_source(
                name
            ),
            str(
                BENT_FABRICATION
            ),
            "exec",
        ),
        namespace,
    )

    return namespace[
        name
    ]


def test_bent_cope_keeps_large_main_tube_not_small_far_side_fragment():
    far_side_fragment = FakeSolid(
        125.0,
        "temporary-fragment",
    )

    bent_tube = FakeSolid(
        12500.0,
        "bent-tube",
    )

    primary_bent_cope_component = (
        loaded_function(
            "_primary_bent_cope_component"
        )
    )

    result = (
        primary_bent_cope_component(
            FakeShape(
                [
                    far_side_fragment,
                    bent_tube,
                ]
            )
        )
    )

    assert result is bent_tube


def test_bent_cope_component_helper_leaves_single_solid_shape_unchanged():
    only = FakeSolid(
        1000.0,
        "only",
    )

    shape = FakeShape(
        [
            only,
        ]
    )

    primary_bent_cope_component = (
        loaded_function(
            "_primary_bent_cope_component"
        )
    )

    assert (
        primary_bent_cope_component(
            shape
        )
        is shape
    )


def test_bent_endpoint_cope_uses_bent_specific_component_retention():
    source = function_source(
        "_apply_bent_endpoint_copes"
    )

    assert (
        "build_through_tube_cutting_tool"
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

    assert (
        "keep_point"
        not in source
    )
