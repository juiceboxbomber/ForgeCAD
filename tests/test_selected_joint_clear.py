from types import SimpleNamespace
import pytest
from forgecad.services.selected_joint_clear import clear_selected_plan, selected_clear_request

class P:
    def __init__(self, x, y, z): self.x, self.y, self.z = x, y, z

def member(ident, a=(0,0,0), b=(1,0,0)):
    return SimpleNamespace(SourceLayoutID=ident, StartPoint=P(*a), EndPoint=P(*b))

def test_selection_resolves_shared_joint_and_order():
    d=member("d",b=(1,1,1)); a=member("a",b=(1,0,0)); b=member("b",b=(0,1,0))
    node, ids=selected_clear_request([d,a,b])
    assert node==(0.0,0.0,0.0) and ids==("d","a","b")

def test_clear_two_diagonal_copes_preserves_miter():
    result=clear_selected_plan(("both_coped",("a","b")),(("d","a"),("d","b"),("x","a")),("d","a","b"),("a","b","d","x"))
    assert result==(False,(("x","a"),),(("d","a"),("d","b")))

def test_clear_exact_miter_pair_preserves_all_copes():
    pairs=(("d","a"),("d","b"))
    result=clear_selected_plan(("both_coped",("a","b")),pairs,("b","a"),("a","b","d"))
    assert result==(True,pairs,())

def test_clear_one_directed_cope_only():
    result=clear_selected_plan(("both_coped",("a","b")),(("d","a"),("d","b")),("d","a"),("a","b","d"))
    assert result==(False,(("d","b"),),(("d","a"),))

def test_through_selection_order_clears_branch_to_through_pair():
    result = clear_selected_plan(
        None, (("d", "a"),), ("a", "d"), ("a", "d")
    )
    assert result == (False, (), (("d", "a"),))

def test_legacy_idless_miter_only_clears_unambiguous_two_member_joint():
    assert clear_selected_plan(("both_coped",()),(),("a","b"),("a","b"))[0] is True
    with pytest.raises(ValueError,match="No matching"):
        clear_selected_plan(("both_coped",()),(),("a","b"),("a","b","d"))

def test_rejects_nonshared_selection():
    a=member("a",(0,0,0),(1,0,0)); b=member("b",(5,0,0),(5,1,0))
    with pytest.raises(ValueError,match="share exactly one"):
        selected_clear_request([a,b])
