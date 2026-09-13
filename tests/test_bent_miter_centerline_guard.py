"""Regression check for opaque centerline stubs used by BentTubeProxy tests."""

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


def test_bent_miter_accepts_opaque_centerline_test_double():
    source = PATH.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    assert (
        "has_solved_centerline"
        in source
    )
    assert (
        'hasattr(\n            centerline,\n            "start_point",'
        in source
    )
    assert (
        'hasattr(\n            centerline,\n            "end_point",'
        in source
    )
    assert (
        'hasattr(\n            centerline,\n            "end_direction",'
        in source
    )
