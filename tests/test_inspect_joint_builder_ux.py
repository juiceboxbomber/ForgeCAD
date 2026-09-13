"""The old builder-UX test name now verifies review-only inspector UX."""

from pathlib import Path


SOURCE = Path("forgecad/adapters/freecad/commands/inspect_joint.py")


def source_text():
    return SOURCE.read_text(encoding="utf-8")


def test_inspector_has_no_fabrication_assignment_controls():
    text = source_text()
    assert "QComboBox" not in text
    assert "Apply Treatment" not in text
    assert "def apply_treatment(" not in text
    assert "treatment_options_for_members" not in text


def test_inspector_advertises_review_only_selection_first_workflow():
    text = source_text()
    assert "Review only" in text
    assert "Saved Fabrication" in text
    assert "Miter Selected" in text
    assert "Cope Selected" in text
    assert "Through Selected" in text
    assert "Clear Selected Treatment" in text


def test_inspector_no_longer_depends_on_failed_compound_ui():
    text = source_text()
    assert "CompoundCopeMixin" not in text
    assert "compound_cope_ui" not in text


def test_connected_member_review_uses_domain_topology():
    text = source_text()
    assert "structural_member_from_freecad_object" in text
    assert "member_touches_node(member, node)" in text
