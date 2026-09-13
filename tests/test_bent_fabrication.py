"""Pure tests for bent-tube fabrication helpers.

This test intentionally avoids importing forgecad.adapters.freecad as a
package because its __init__ imports FreeCAD's Part module, which is not
available in the normal local CPython pytest environment.
"""

import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "bent_fabrication.py"
)


def _function_source(
    source,
    tree,
    name,
):
    node = next(
        item
        for item
        in tree.body
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


def _load_helpers():
    source = PATH.read_text(
        encoding="utf-8"
    )
    tree = ast.parse(
        source
    )

    namespace = {}

    exec(
        _function_source(
            source,
            tree,
            "_numeric",
        ),
        namespace,
    )

    exec(
        _function_source(
            source,
            tree,
            "_miter_cutter_size",
        ),
        namespace,
    )

    return namespace[
        "_miter_cutter_size"
    ]


def test_miter_cutter_size_covers_curved_shape_bounds():
    miter_cutter_size = (
        _load_helpers()
    )

    shape = SimpleNamespace(
        BoundBox=SimpleNamespace(
            XLength=1200.0,
            YLength=800.0,
            ZLength=50.0,
        )
    )

    profile = SimpleNamespace(
        outside_diameter=44.45
    )

    assert (
        miter_cutter_size(
            shape,
            profile,
        )
        == 4800.0
    )


def test_miter_cutter_size_falls_back_to_tube_diameter():
    miter_cutter_size = (
        _load_helpers()
    )

    shape = SimpleNamespace(
        BoundBox=None
    )

    profile = SimpleNamespace(
        outside_diameter=50.8
    )

    assert (
        miter_cutter_size(
            shape,
            profile,
        )
        == 203.2
    )
