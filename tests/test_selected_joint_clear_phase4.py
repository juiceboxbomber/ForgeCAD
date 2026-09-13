from types import SimpleNamespace

from forgecad.services.selected_joint_clear import (
    clear_selected_operation_plan,
    selected_clear_request,
)


class P:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z


def member(ident, a, b):
    return SimpleNamespace(SourceLayoutID=ident, StartPoint=P(*a), EndPoint=P(*b))


def test_clear_request_accepts_through_first_interior_t_joint():
    main = member("main", (-10, 0, 0), (10, 0, 0))
    branch = member("branch", (0, 0, 0), (0, 10, 0))
    node, ids = selected_clear_request([main, branch])
    assert node == (0.0, 0.0, 0.0)
    assert ids == ("main", "branch")


def test_clear_dedicated_through_does_not_touch_generic_cope():
    result = clear_selected_operation_plan(
        None,
        (("diag", "rail"),),
        ("main", "branch"),
        ("main", "branch", "diag", "rail"),
        (("branch", "main"),),
    )
    assert result == (
        False,
        (("diag", "rail"),),
        (),
        (),
        (("branch", "main"),),
    )


def test_phase3_legacy_through_in_generic_cope_can_be_cleared():
    result = clear_selected_operation_plan(
        None,
        (("branch", "main"),),
        ("main", "branch"),
        ("main", "branch"),
        (),
    )
    assert result[1] == ()
    assert result[2] == (("branch", "main"),)
