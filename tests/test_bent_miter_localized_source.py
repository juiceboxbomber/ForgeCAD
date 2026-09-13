"""Source regression for bent miter localization.

A curved tube must not use the full-shape bounding box as its miter cutter
extent because distant portions of the same tube can cross the end miter plane.
"""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "bent_fabrication.py"
)


def test_bent_miter_is_localized_to_each_endpoint():
    source = PATH.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    start = source.index(
        "def apply_bent_miter_shape("
    )

    function = source[
        start:
    ]

    assert (
        "start_cutter_size"
        in function
    )
    assert (
        "end_cutter_size"
        in function
    )
    assert (
        "_endpoint_run_lengths"
        in function
    )
