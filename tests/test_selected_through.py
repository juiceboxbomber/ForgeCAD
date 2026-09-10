from types import SimpleNamespace
import pytest

from forgecad.services.selected_through import (
    replace_branch_pairs,
    selected_through_request,
    validate_primary_compatibility,
)


class P:
    def __init__(self, x, y, z): self.x, self.y, self.z = x, y, z


def member(ident, a=(0,0,0), b=(1,0,0)):
    return SimpleNamespace(SourceLayoutID=ident, StartPoint=P(*a), EndPoint=P(*b))


def test_first_selection_is_through_and_remaining_are_branches():
    t=member("through",b=(10,0,0)); a=member("a",b=(0,10,0)); b=member("b",b=(0,0,10))
    node, through, branches=selected_through_request([t,a,b])
    assert node==(0.0,0.0,0.0)
    assert through=="through" and branches==("a","b")


def test_all_selected_tubes_must_share_one_joint():
    a=member("a",(0,0,0),(1,0,0)); b=member("b",(5,0,0),(5,1,0))
    with pytest.raises(ValueError,match="share exactly one"):
        selected_through_request([a,b])


def test_selected_branches_are_retargeted_without_touching_other_sources():
    result=replace_branch_pairs(
        (("a","old"),("x","keep"),("b","other")),
        "through",("a","b")
    )
    assert result==(("x","keep"),("a","through"),("b","through"))


def test_unrelated_saved_miter_is_preserved():
    validate_primary_compatibility(("both_coped",("m1","m2")),("through","branch"))


def test_selected_member_cannot_still_belong_to_miter():
    with pytest.raises(ValueError,match="part of this joint's miter"):
        validate_primary_compatibility(("both_coped",("through","m2")),("through","branch"))


def test_legacy_idless_miter_is_not_guessed():
    with pytest.raises(ValueError,match="legacy miter"):
        validate_primary_compatibility(("both_coped",()),("through","branch"))


def test_legacy_joint_wide_through_requires_manual_migration():
    with pytest.raises(ValueError,match="legacy joint-wide Through"):
        validate_primary_compatibility(("member_through",("through",)),("through","branch"))
