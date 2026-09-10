"""Tests for strict selection-first relationship persistence validation."""

import pytest

from forgecad.adapters.freecad.joint_pair_validation import normalized_pairs


def test_normalized_pairs_preserves_direction_order_and_deduplicates():
    assert normalized_pairs(((" branch ", "main"), ("branch", "main"), ("x", "y"))) == (
        ("branch", "main"),
        ("x", "y"),
    )


@pytest.mark.parametrize(
    "pairs",
    (
        (("a", "a"),),
        (("", "b"),),
        (("a", ""),),
        (("a",),),
        (("a", "b", "c"),),
        ("not-a-pair",),
    ),
)
def test_normalized_pairs_rejects_malformed_relationships(pairs):
    with pytest.raises(ValueError):
        normalized_pairs(pairs)
