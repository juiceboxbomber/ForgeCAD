"""Regression checks for the selection-first joint cleanup."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREECAD = ROOT / "forgecad" / "adapters" / "freecad"


def test_obsolete_compound_inspector_modules_are_removed():
    assert not (FREECAD / "compound_cope_ui.py").exists()
    assert not (FREECAD / "compound_cope_selection.py").exists()


def test_runtime_code_has_no_obsolete_compound_inspector_imports():
    offenders = []
    for path in (ROOT / "forgecad").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if (
            "forgecad.adapters.freecad.compound_cope_ui" in text
            or "forgecad.adapters.freecad.compound_cope_selection" in text
        ):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_pair_store_uses_neutral_selection_first_validator():
    text = (FREECAD / "joint_treatment_store.py").read_text(encoding="utf-8")
    assert "forgecad.adapters.freecad.joint_pair_validation" in text
