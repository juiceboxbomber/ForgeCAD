from types import SimpleNamespace
import pytest

from forgecad.services.selected_through import (
    branch_joint_point,
    remove_source_pairs,
    replace_branch_pairs,
    selected_joint_point,
    selected_through_request,
)


class P:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z


def member(ident, a=(0, 0, 0), b=(1, 0, 0)):
    return SimpleNamespace(SourceLayoutID=ident, StartPoint=P(*a), EndPoint=P(*b))


def test_corner_is_still_supported():
    main = member("main", (0, 0, 0), (10, 0, 0))
    branch = member("branch", (0, 0, 0), (0, 10, 0))
    node, through, branches = selected_through_request([main, branch])
    assert node == (0.0, 0.0, 0.0)
    assert through == "main"
    assert branches == ("branch",)


def test_branch_endpoint_on_main_interior_is_supported():
    main = member("main", (-10, 0, 0), (10, 0, 0))
    branch = member("branch", (0, 0, 0), (0, 10, 0))
    assert branch_joint_point(main, branch) == (0.0, 0.0, 0.0)
    node, through, branches = selected_through_request([main, branch])
    assert node == (0.0, 0.0, 0.0)
    assert through == "main"
    assert branches == ("branch",)


def test_two_branch_pieces_can_meet_same_interior_t_joint():
    main = member("main", (-10, 0, 0), (10, 0, 0))
    upper = member("upper", (0, 0, 0), (0, 10, 0))
    lower = member("lower", (0, 0, 0), (0, -10, 0))
    node, through, branches = selected_through_request([main, upper, lower])
    assert node == (0.0, 0.0, 0.0)
    assert branches == ("upper", "lower")


def test_continuous_crossing_branch_gets_specific_message():
    main = member("main", (-10, 0, 0), (10, 0, 0))
    crossing = member("cross", (0, -10, 0), (0, 10, 0))
    with pytest.raises(ValueError, match="Both selected tubes continue through"):
        selected_through_request([main, crossing])


def test_reverse_t_order_explains_that_second_tube_is_continuous():
    short = member("short", (0, 0, 0), (0, 10, 0))
    continuous = member("continuous", (-10, 0, 0), (10, 0, 0))
    with pytest.raises(ValueError, match="second tube continues through"):
        selected_through_request([short, continuous])


def test_branches_at_different_points_are_rejected():
    main = member("main", (-10, 0, 0), (10, 0, 0))
    a = member("a", (-2, 0, 0), (-2, 10, 0))
    b = member("b", (2, 0, 0), (2, 10, 0))
    with pytest.raises(ValueError, match="same joint"):
        selected_through_request([main, a, b])


def test_generic_joint_point_accepts_endpoint_to_interior_for_clear():
    main = member("main", (-10, 0, 0), (10, 0, 0))
    branch = member("branch", (0, 0, 0), (0, 10, 0))
    assert selected_joint_point([main, branch]) == (0.0, 0.0, 0.0)


def test_phase3_generic_through_pair_can_be_migrated():
    generic = (("branch", "main"), ("other", "target"))
    assert remove_source_pairs(generic, ("branch",)) == (("other", "target"),)
    assert replace_branch_pairs((), "main", ("branch",)) == (("branch", "main"),)
