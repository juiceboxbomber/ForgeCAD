"""Selection tests for straight-member cope against bent targets."""

from types import SimpleNamespace

import pytest

from forgecad.services.selected_cope import (
    selected_cope_request,
)


def point(x, y, z=0.0):
    return SimpleNamespace(
        x=x,
        y=y,
        z=z,
    )


def node(x, y, z=0.0):
    return SimpleNamespace(
        Position=point(
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
        StartPoint=point(
            *start
        ),
        EndPoint=point(
            *end
        ),
    )


def bent(
    start_id="B-START",
    end_id="B-END",
):
    return SimpleNamespace(
        StartNode=node(
            0.0,
            0.0,
            0.0,
        ),
        EndNode=node(
            600.0,
            600.0,
            0.0,
        ),
        StartFabricationLayoutID=start_id,
        EndFabricationLayoutID=end_id,
        SourceLayoutLines=(),
    )


def test_straight_source_can_cope_to_bent_start_endpoint():
    source = straight(
        "S",
        (0.0, 0.0, 0.0),
        (-500.0, 200.0, 0.0),
    )

    node_xyz, source_id, target_ids = (
        selected_cope_request(
            [
                source,
                bent(),
            ]
        )
    )

    assert node_xyz == (
        0.0,
        0.0,
        0.0,
    )
    assert source_id == "S"
    assert target_ids == (
        "B-START",
    )


def test_straight_source_can_cope_to_bent_end_endpoint():
    source = straight(
        "S",
        (600.0, 600.0, 0.0),
        (900.0, 900.0, 0.0),
    )

    node_xyz, source_id, target_ids = (
        selected_cope_request(
            [
                source,
                bent(),
            ]
        )
    )

    assert node_xyz == (
        600.0,
        600.0,
        0.0,
    )
    assert source_id == "S"
    assert target_ids == (
        "B-END",
    )


def test_bent_source_is_not_enabled_in_target_only_phase():
    with pytest.raises(
        ValueError,
        match="Bent tubes are supported as cope targets first",
    ):
        selected_cope_request(
            [
                bent(),
                straight(
                    "S",
                    (0.0, 0.0, 0.0),
                    (-500.0, 0.0, 0.0),
                ),
            ]
        )
