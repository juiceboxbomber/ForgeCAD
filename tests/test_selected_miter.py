from types import SimpleNamespace

import pytest

from forgecad.services.selected_miter import selected_miter_request


class P:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z


def member(ident, a, b, **extra):
    values = dict(SourceLayoutID=ident, StartPoint=P(*a), EndPoint=P(*b))
    values.update(extra)
    return SimpleNamespace(**values)


def test_pair_can_be_selected_from_larger_compound_joint_without_metadata_filtering():
    first = member("rail-a", (0, 0, 0), (100, 0, 0), StartCopeEnabled=True)
    second = member("rail-b", (0, 0, 0), (0, 100, 0), EndMiterEnabled=True)

    node, ids = selected_miter_request([first, second])

    assert node == (0.0, 0.0, 0.0)
    assert ids == ("rail-a", "rail-b")


def test_requires_exactly_two_members():
    first = member("a", (0, 0, 0), (1, 0, 0))
    second = member("b", (0, 0, 0), (0, 1, 0))
    third = member("c", (0, 0, 0), (0, 0, 1))

    with pytest.raises(ValueError, match="exactly two"):
        selected_miter_request([first, second, third])


def test_requires_one_shared_endpoint():
    first = member("a", (0, 0, 0), (1, 0, 0))
    second = member("b", (5, 0, 0), (5, 1, 0))

    with pytest.raises(ValueError, match="share exactly one"):
        selected_miter_request([first, second])


def test_rejects_missing_persistent_identity():
    first = member("a", (0, 0, 0), (1, 0, 0))
    second = SimpleNamespace(StartPoint=P(0, 0, 0), EndPoint=P(0, 1, 0))

    with pytest.raises(ValueError, match="SourceLayoutID"):
        selected_miter_request([first, second])
