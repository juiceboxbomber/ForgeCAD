"""Source checks for physical endpoint stock on bent miters."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAB = ROOT / "forgecad/adapters/freecad/bent_fabrication.py"
BENT = ROOT / "forgecad/adapters/freecad/bent_tube_object.py"


def test_bent_fabrication_adds_extension_stock():
    source = FAB.read_text(encoding="utf-8")
    ast.parse(source)
    assert "StartExtension" in source
    assert "EndExtension" in source
    assert "build_tube_shape" in source
    assert "centerline.end_direction" in source
    assert ".fuse(" in source


def test_bent_proxy_passes_centerline_to_fabrication():
    source = BENT.read_text(encoding="utf-8")
    ast.parse(source)
    assert "centerline=centerline" in source
