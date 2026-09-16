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


def test_bent_source_start_can_cope_to_straight_target():
    source = bent()

    target = straight(
        "S",
        (0.0, 0.0, 0.0),
        (-500.0, 200.0, 0.0),
    )

    node_xyz, source_id, target_ids = (
        selected_cope_request(
            [
                source,
                target,
            ]
        )
    )

    assert node_xyz == (
        0.0,
        0.0,
        0.0,
    )
    assert source_id == "B-START"
    assert target_ids == (
        "S",
    )


def test_bent_source_end_can_cope_to_straight_target():
    source = bent()

    target = straight(
        "S",
        (600.0, 600.0, 0.0),
        (900.0, 900.0, 0.0),
    )

    node_xyz, source_id, target_ids = (
        selected_cope_request(
            [
                source,
                target,
            ]
        )
    )

    assert node_xyz == (
        600.0,
        600.0,
        0.0,
    )
    assert source_id == "B-END"
    assert target_ids == (
        "S",
    )


def test_bent_source_can_cope_to_bent_target_at_shared_endpoint():
    source = bent(
        "SOURCE-START",
        "SOURCE-END",
    )

    target = bent(
        "TARGET-START",
        "TARGET-END",
    )

    # The two bent tubes must share exactly one physical endpoint.
    # bent() uses the same canonical start/end geometry for convenience,
    # so move the target's far endpoint away from the source.
    target.EndNode = node(
        900.0,
        -300.0,
        0.0,
    )

    node_xyz, source_id, target_ids = (
        selected_cope_request(
            [
                source,
                target,
            ]
        )
    )

    assert node_xyz == (
        0.0,
        0.0,
        0.0,
    )

    assert source_id == (
        "SOURCE-START"
    )

    assert target_ids == (
        "TARGET-START",
    )
