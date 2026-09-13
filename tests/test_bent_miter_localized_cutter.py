"""Tests for end-local bent-tube miter cutter sizing."""

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


def _load_size_helper():
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
            "_local_miter_cutter_size",
        ),
        namespace,
    )

    return namespace[
        "_local_miter_cutter_size"
    ]


def test_local_cutter_does_not_scale_with_entire_bent_shape():
    size = _load_size_helper()

    profile = SimpleNamespace(
        outside_diameter=44.45
    )

    result = size(
        profile,
        extension_mm=22.225,
        straight_run_length=1000.0,
    )

    # Old whole-shape sizing on a ~1200 mm frame was about 4800 mm.
    # The new end-local cutter must stay hundreds of millimeters, not thousands.
    assert result < 500.0


def test_local_cutter_is_large_enough_to_remove_extension_tail():
    size = _load_size_helper()

    profile = SimpleNamespace(
        outside_diameter=44.45
    )

    result = size(
        profile,
        extension_mm=150.0,
        straight_run_length=800.0,
    )

    assert result > (
        150.0
        + 2.0 * 44.45
    )


def test_apply_bent_miter_uses_separate_start_and_end_cutter_sizes():
    source = PATH.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    assert (
        "start_cutter_size"
        in source
    )
    assert (
        "end_cutter_size"
        in source
    )
    assert (
        "_local_miter_cutter_size"
        in source
    )

    apply_start = source.index(
        "def apply_bent_miter_shape("
    )

    function_source = source[
        apply_start:
    ]

    # Match only a direct call to the old helper. The substring
    # "_miter_cutter_size(" also appears inside the intended
    # "_local_miter_cutter_size(" name.
    import re

    assert (
        re.search(
            r"(?<![A-Za-z0-9_])_miter_cutter_size\(",
            function_source,
        )
        is None
    )
