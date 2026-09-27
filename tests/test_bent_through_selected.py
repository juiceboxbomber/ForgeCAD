"""Bent-member selection regressions for Through Selected."""

from types import SimpleNamespace

import pytest

from forgecad.services.selected_through import (
    selected_through_request,
)


class P:
    def __init__(
        self,
        x,
        y,
        z=0.0,
    ):
        self.x = x
        self.y = y
        self.z = z


def node(
    x,
    y,
    z=0.0,
):
    return SimpleNamespace(
        Position=P(
            x,
            y,
            z,
        )
    )


def straight(
    ident,
    start,
    end,
):
    return SimpleNamespace(
        SourceLayoutID=ident,
        StartPoint=P(
            *start
        ),
        EndPoint=P(
            *end
        ),
    )


def bent(
    start_id,
    end_id,
    start,
    end,
):
    return SimpleNamespace(
        StartNode=node(
            *start
        ),
        EndNode=node(
            *end
        ),
        StartFabricationLayoutID=start_id,
        EndFabricationLayoutID=end_id,
        SourceLayoutLines=(),
    )


def test_straight_through_accepts_bent_branch_start_on_interior():
    through = straight(
        "THROUGH",
        (0.0, 0.0, 0.0),
        (1000.0, 0.0, 0.0),
    )

    branch = bent(
        "B-START",
        "B-END",
        (500.0, 0.0, 0.0),
        (750.0, 300.0, 0.0),
    )

    result = selected_through_request(
        [
            through,
            branch,
        ]
    )

    assert result == (
        (500.0, 0.0, 0.0),
        "THROUGH",
        (
            "B-START",
        ),
    )


def test_straight_through_accepts_bent_branch_end_on_interior():
    through = straight(
        "THROUGH",
        (0.0, 0.0, 0.0),
        (1000.0, 0.0, 0.0),
    )

    branch = bent(
        "B-START",
        "B-END",
        (750.0, 300.0, 0.0),
        (500.0, 0.0, 0.0),
    )

    result = selected_through_request(
        [
            through,
            branch,
        ]
    )

    assert result[
        0
    ] == (
        500.0,
        0.0,
        0.0,
    )

    assert result[
        2
    ] == (
        "B-END",
    )


def test_bent_through_start_accepts_straight_branch_endpoint():
    through = bent(
        "T-START",
        "T-END",
        (0.0, 0.0, 0.0),
        (700.0, 700.0, 0.0),
    )

    branch = straight(
        "BRANCH",
        (0.0, 0.0, 0.0),
        (-400.0, 200.0, 0.0),
    )

    assert selected_through_request(
        [
            through,
            branch,
        ]
    ) == (
        (0.0, 0.0, 0.0),
        "T-START",
        (
            "BRANCH",
        ),
    )


def test_bent_through_end_accepts_straight_branch_endpoint():
    through = bent(
        "T-START",
        "T-END",
        (0.0, 0.0, 0.0),
        (700.0, 700.0, 0.0),
    )

    branch = straight(
        "BRANCH",
        (700.0, 700.0, 0.0),
        (1000.0, 500.0, 0.0),
    )

    result = selected_through_request(
        [
            through,
            branch,
        ]
    )

    assert result[
        1
    ] == "T-END"


def test_bent_through_accepts_bent_branch_at_true_endpoint():
    through = bent(
        "T-START",
        "T-END",
        (0.0, 0.0, 0.0),
        (700.0, 700.0, 0.0),
    )

    branch = bent(
        "B-START",
        "B-END",
        (0.0, 0.0, 0.0),
        (-500.0, 300.0, 0.0),
    )

    assert selected_through_request(
        [
            through,
            branch,
        ]
    ) == (
        (0.0, 0.0, 0.0),
        "T-START",
        (
            "B-START",
        ),
    )


def test_bent_through_rejects_point_on_start_to_end_chord_interior():
    through = bent(
        "T-START",
        "T-END",
        (0.0, 0.0, 0.0),
        (1000.0, 1000.0, 0.0),
    )

    branch = straight(
        "BRANCH",
        (500.0, 500.0, 0.0),
        (500.0, 800.0, 0.0),
    )

    with pytest.raises(
        ValueError,
        match="start-to-end chord is not tube geometry",
    ):
        selected_through_request(
            [
                through,
                branch,
            ]
        )


def test_bent_branch_does_not_use_its_start_to_end_chord_as_branch_geometry():
    through = straight(
        "THROUGH",
        (0.0, 0.0, 0.0),
        (1000.0, 0.0, 0.0),
    )

    # The imaginary chord crosses the through member, but neither real bent
    # endpoint lands on it.
    branch = bent(
        "B-START",
        "B-END",
        (500.0, -300.0, 0.0),
        (500.0, 300.0, 0.0),
    )

    with pytest.raises(
        ValueError,
        match="true physical StartNode or EndNode",
    ):
        selected_through_request(
            [
                through,
                branch,
            ]
        )


def test_straight_only_interior_t_joint_remains_supported():
    through = straight(
        "THROUGH",
        (0.0, 0.0, 0.0),
        (1000.0, 0.0, 0.0),
    )

    branch = straight(
        "BRANCH",
        (500.0, 0.0, 0.0),
        (500.0, 300.0, 0.0),
    )

    assert selected_through_request(
        [
            through,
            branch,
        ]
    ) == (
        (500.0, 0.0, 0.0),
        "THROUGH",
        (
            "BRANCH",
        ),
    )
