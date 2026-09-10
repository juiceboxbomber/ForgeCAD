from types import SimpleNamespace
import pytest

from forgecad.services.selected_cope import replace_source_pairs, selected_cope_request


class P:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z


def member(ident, a, b, **extra):
    values = dict(SourceLayoutID=ident, StartPoint=P(*a), EndPoint=P(*b))
    values.update(extra)
    return SimpleNamespace(**values)


def test_mitered_members_are_valid_targets():
    source = member("diag", (0,0,0), (10,10,10))
    target_a = member("rail-a", (0,0,0), (100,0,0), StartMiterEnabled=True)
    target_b = member("rail-b", (0,0,0), (0,100,0), EndMiterEnabled=True)
    node, source_id, targets = selected_cope_request([source, target_a, target_b])
    assert node == (0.0, 0.0, 0.0)
    assert source_id == "diag"
    assert targets == ("rail-a", "rail-b")


def test_selection_order_defines_source():
    source = member("d", (0,0,0), (1,1,1))
    target = member("m", (0,0,0), (5,0,0))
    _, source_id, targets = selected_cope_request([source, target])
    assert source_id == "d"
    assert targets == ("m",)


def test_requires_common_joint():
    a = member("a", (0,0,0), (1,0,0))
    b = member("b", (5,0,0), (6,0,0))
    with pytest.raises(ValueError, match="share exactly one joint"):
        selected_cope_request([a,b])


def test_replaces_only_selected_sources_old_copes():
    result = replace_source_pairs(
        (("diag", "wrong"), ("other", "target")),
        "diag",
        ("miter-a", "miter-b"),
    )
    assert result == (
        ("other", "target"),
        ("diag", "miter-a"),
        ("diag", "miter-b"),
    )
