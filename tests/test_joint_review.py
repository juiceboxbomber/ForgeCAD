"""Tests for read-only joint fabrication review rows."""

import pytest

from forgecad.services.joint_review import fabrication_rows


def names():
    return {
        "a": "M011 - Upper Left",
        "b": "M012 - Upper Right",
        "d": "M014 - Diagonal",
    }


def test_automatic_joint_has_one_read_only_row():
    assert fabrication_rows(None, (), (), names()) == (
        ("Automatic", "—", "No manual fabrication operation saved"),
    )


def test_saved_miter_reports_exact_pair():
    assert fabrication_rows(("both_coped", ("a", "b")), (), (), names()) == (
        ("Miter", "M011 - Upper Left", "M012 - Upper Right"),
    )


def test_miter_cope_and_through_can_be_reviewed_together():
    rows = fabrication_rows(
        ("both_coped", ("a", "b")),
        (("d", "a"),),
        (("d", "b"),),
        names(),
    )
    assert rows == (
        ("Miter", "M011 - Upper Left", "M012 - Upper Right"),
        ("Cope", "M014 - Diagonal", "M011 - Upper Left"),
        ("Through", "M012 - Upper Right", "Branch: M014 - Diagonal"),
    )


def test_unknown_layout_id_stays_visible_instead_of_becoming_member():
    assert fabrication_rows(("both_coped", ("a", "missing")), (), (), names())[0] == (
        "Miter", "M011 - Upper Left", "missing"
    )


def test_legacy_member_through_is_marked_as_legacy():
    assert fabrication_rows(("member_through", ("a",)), (), (), names()) == (
        ("Legacy Through", "M011 - Upper Left", "Primary joint treatment"),
    )


def test_malformed_additive_relationship_is_rejected():
    with pytest.raises(ValueError, match="malformed"):
        fabrication_rows(None, (("a", "a"),), (), names())
