"""Bent-member Clear Selected selection regression tests."""

from types import SimpleNamespace

import pytest

from forgecad.services.selected_joint_clear import (
    selected_clear_request,
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


def bent():
    return SimpleNamespace(
        SourceLayoutID="",
        StartNode=node(
            0.0,
            0.0,
        ),
        EndNode=node(
            1000.0,
            1000.0,
        ),
        StartFabricationLayoutID="L-A",
        EndFabricationLayoutID="L-B",
        SourceLayoutLines=(),
    )


def test_clear_selected_resolves_bent_end_identity():
    member = bent()

    rail = straight(
        "L-C",
        (
            1000.0,
            1000.0,
            0.0,
        ),
        (
            1500.0,
            1000.0,
            0.0,
        ),
    )

    point, ids = selected_clear_request(
        [
            member,
            rail,
        ]
    )

    assert point == pytest.approx(
        (
            1000.0,
            1000.0,
            0.0,
        )
    )

    assert ids == (
        "L-B",
        "L-C",
    )


def test_clear_selected_resolves_other_bent_end_independently():
    member = bent()

    rail = straight(
        "L-Z",
        (
            -500.0,
            0.0,
            0.0,
        ),
        (
            0.0,
            0.0,
            0.0,
        ),
    )

    point, ids = selected_clear_request(
        [
            member,
            rail,
        ]
    )

    assert point == pytest.approx(
        (
            0.0,
            0.0,
            0.0,
        )
    )

    assert ids == (
        "L-A",
        "L-Z",
    )


def test_bent_selection_never_uses_chord_as_joint():
    member = bent()

    crossing = straight(
        "L-X",
        (
            500.0,
            500.0,
            0.0,
        ),
        (
            500.0,
            1500.0,
            0.0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="share exactly one joint endpoint",
    ):
        selected_clear_request(
            [
                member,
                crossing,
            ]
        )


def test_straight_through_interior_fallback_is_preserved():
    main = straight(
        "main",
        (
            -10.0,
            0.0,
            0.0,
        ),
        (
            10.0,
            0.0,
            0.0,
        ),
    )

    branch = straight(
        "branch",
        (
            0.0,
            0.0,
            0.0,
        ),
        (
            0.0,
            10.0,
            0.0,
        ),
    )

    point, ids = selected_clear_request(
        [
            main,
            branch,
        ]
    )

    assert point == pytest.approx(
        (
            0.0,
            0.0,
            0.0,
        )
    )

    assert ids == (
        "main",
        "branch",
    )
