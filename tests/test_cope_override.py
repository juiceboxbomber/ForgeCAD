from types import SimpleNamespace
from forgecad.services.cope_override import merge_direct_cope_specifications


def spec(member, end, target):
    return SimpleNamespace(coped_member=member,coped_end=end,target_member=target)


def test_direct_spec_replaces_automatic_spec_on_same_member_end():
    branch=object(); old_target=object(); new_target=object(); other=object()
    automatic=(spec(branch,"start",old_target),spec(other,"start",old_target))
    direct=(spec(branch,"start",new_target),)
    result=merge_direct_cope_specifications(automatic,direct)
    assert len(result)==2
    assert result[0].coped_member is other
    assert result[1] is direct[0]


def test_two_direct_copes_on_same_end_are_both_retained():
    branch=object(); a=object(); b=object(); automatic_target=object()
    direct=(spec(branch,"end",a),spec(branch,"end",b))
    result=merge_direct_cope_specifications((spec(branch,"end",automatic_target),),direct)
    assert result==direct


def test_unrelated_primary_specs_are_unchanged():
    a=object(); b=object(); target=object()
    primary=(spec(a,"start",target),spec(b,"end",target))
    assert merge_direct_cope_specifications(primary,())==primary
