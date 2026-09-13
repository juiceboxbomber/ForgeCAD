from types import SimpleNamespace
from forgecad.services.selected_cope import selected_cope_request, replace_source_pairs
class P:
    def __init__(self,x,y,z): self.x,self.y,self.z=x,y,z
def m(i,a,b): return SimpleNamespace(SourceLayoutID=i,StartPoint=P(*a),EndPoint=P(*b))
def test_three_targets():
    d=m("d",(0,0,0),(1,1,1)); u=m("u",(0,0,0),(0,0,5)); a=m("a",(0,0,0),(5,0,0)); b=m("b",(0,0,0),(0,5,0))
    node,source,targets=selected_cope_request([d,u,a,b])
    assert node==(0.0,0.0,0.0); assert source=="d"; assert targets==("u","a","b")
def test_replace_all_three_at_once():
    assert replace_source_pairs((("d","old"),("x","y")),"d",("u","a","b")) == (("x","y"),("d","u"),("d","a"),("d","b"))

def test_clear_plan_can_remove_all_three_direct_copes():
    from forgecad.services.selected_joint_clear import clear_selected_operation_plan
    result=clear_selected_operation_plan(
        None,
        (("d","u"),("d","a"),("d","b"),("x","y")),
        ("d","u","a","b"),
        ("d","u","a","b","x","y"),
        (),
    )
    assert result[1] == (("x","y"),)
    assert result[2] == (("d","u"),("d","a"),("d","b"))
