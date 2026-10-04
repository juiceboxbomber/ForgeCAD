"""Bent-source -> bent-target Trim / Extend geometry regressions."""

import pytest

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Material,
    Node,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import Vector3D
from forgecad.services.member_trim_extend import (
    bent_to_bent_endpoint_intersection_3d,
)


def profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def material():
    return Material(
        name="DOM Steel",
        density=7850.0,
        yield_strength=350.0,
    )


def bent(
    start,
    end,
    direction,
):
    return BentMember(
        start=start,
        end=end,
        tube=BentTube(
            straight_runs=(
                StraightRun(
                    100.0
                ),
                StraightRun(
                    120.0
                ),
            ),
            bends=(
                Bend(
                    angle_degrees=90.0,
                    centerline_radius=50.0,
                ),
            ),
            profile=profile(),
            material=material(),
        ),
        initial_direction=direction,
        initial_bend_normal=Vector3D(
            0.0,
            0.0,
            1.0,
        ),
    )


def test_bent_source_can_extend_to_bent_target_start_tangent():
    source = bent(
        Node(
            0.0,
            -20.0,
            0.0,
        ),
        Node(
            170.0,
            130.0,
            0.0,
        ),
        Vector3D(
            0.0,
            -1.0,
            0.0,
        ),
    )

    target = bent(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            150.0,
            170.0,
            0.0,
        ),
        Vector3D(
            1.0,
            0.0,
            0.0,
        ),
    )

    intersection, distance, _, kind = (
        bent_to_bent_endpoint_intersection_3d(
            source,
            target,
            "start",
            "start",
        )
    )

    assert intersection == Node(
        0.0,
        0.0,
        0.0,
    )

    assert distance == pytest.approx(
        20.0
    )

    assert kind == "extend"


def test_bent_source_can_trim_to_bent_target_start_tangent():
    source = bent(
        Node(
            0.0,
            20.0,
            0.0,
        ),
        Node(
            170.0,
            170.0,
            0.0,
        ),
        Vector3D(
            0.0,
            -1.0,
            0.0,
        ),
    )

    target = bent(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            150.0,
            170.0,
            0.0,
        ),
        Vector3D(
            1.0,
            0.0,
            0.0,
        ),
    )

    intersection, distance, _, kind = (
        bent_to_bent_endpoint_intersection_3d(
            source,
            target,
            "start",
            "start",
        )
    )

    assert intersection == Node(
        0.0,
        0.0,
        0.0,
    )

    assert distance == pytest.approx(
        -20.0
    )

    assert kind == "trim"


def test_bent_to_bent_requires_both_physical_endpoints():
    source = bent(
        Node(
            0.0,
            -20.0,
            0.0,
        ),
        Node(
            170.0,
            130.0,
            0.0,
        ),
        Vector3D(
            0.0,
            -1.0,
            0.0,
        ),
    )

    target = bent(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            150.0,
            170.0,
            0.0,
        ),
        Vector3D(
            1.0,
            0.0,
            0.0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="bent source",
    ):
        bent_to_bent_endpoint_intersection_3d(
            source,
            target,
            None,
            "start",
        )

    with pytest.raises(
        ValueError,
        match="bent target",
    ):
        bent_to_bent_endpoint_intersection_3d(
            source,
            target,
            "start",
            None,
        )
