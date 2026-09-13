"""Source regression for disconnected bent-miter stock fragments."""

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


def test_each_bent_miter_discards_disconnected_outside_fragment():
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
        "primary_cope_component"
        in function
    )

    assert (
        function.count(
            "primary_cope_component("
        )
        >= 2
    )

    assert (
        "obj.StartMiterKeepPoint"
        in function
    )

    assert (
        "obj.EndMiterKeepPoint"
        in function
    )
