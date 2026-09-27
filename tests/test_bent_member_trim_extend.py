"""Bent-member Trim / Extend geometry regressions."""

import pytest

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Material,
    Member,
    Node,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import Vector3D
from forgecad.services.member_trim_extend import (
    bent_endpoint_intersection_3d,
)


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def make_material():
    return Material(
        name="DOM Steel",
        density=7850.0,
        yield_strength=350.0,
    )


def make_bent_member():
    tube = BentTube(
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
        profile=make_profile(),
        material=make_material(),
    )

    return BentMember(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            150.0,
            170.0,
            0.0,
        ),
        tube=tube,
        initial_direction=Vector3D(
            1.0,
            0.0,
            0.0,
        ),
        initial_bend_normal=Vector3D(
            0.0,
            0.0,
            1.0,
        ),
    )


def vertical_target(
    x,
):
    return Member(
        start=Node(
            x,
            -500.0,
            0.0,
        ),
        end=Node(
            x,
            500.0,
            0.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )


def horizontal_target(
    y,
):
    return Member(
        start=Node(
            -500.0,
            y,
            0.0,
        ),
        end=Node(
            500.0,
            y,
            0.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )


def test_start_extension_uses_start_local_tangent():
    intersection, distance, _, kind = (
        bent_endpoint_intersection_3d(
            make_bent_member(),
            vertical_target(
                -40.0
            ),
            "start",
        )
    )

    assert intersection == Node(
        -40.0,
        0.0,
        0.0,
    )
    assert distance == pytest.approx(
        40.0
    )
    assert kind == "extend"


def test_start_trim_uses_start_local_tangent():
    intersection, distance, _, kind = (
        bent_endpoint_intersection_3d(
            make_bent_member(),
            vertical_target(
                25.0
            ),
            "start",
        )
    )

    assert intersection == Node(
        25.0,
        0.0,
        0.0,
    )
    assert distance == pytest.approx(
        -25.0
    )
    assert kind == "trim"


def test_start_trim_cannot_reach_nearest_bend():
    with pytest.raises(
        ValueError,
        match="nearest bend",
    ):
        bent_endpoint_intersection_3d(
            make_bent_member(),
            vertical_target(
                100.0
            ),
            "start",
        )


def test_end_extension_uses_end_local_tangent():
    intersection, distance, _, kind = (
        bent_endpoint_intersection_3d(
            make_bent_member(),
            horizontal_target(
                210.0
            ),
            "end",
        )
    )

    assert intersection == Node(
        150.0,
        210.0,
        0.0,
    )
    assert distance == pytest.approx(
        40.0
    )
    assert kind == "extend"


def test_end_trim_uses_end_local_tangent():
    intersection, distance, _, kind = (
        bent_endpoint_intersection_3d(
            make_bent_member(),
            horizontal_target(
                150.0
            ),
            "end",
        )
    )

    assert intersection == Node(
        150.0,
        150.0,
        0.0,
    )
    assert distance == pytest.approx(
        -20.0
    )
    assert kind == "trim"


def test_bent_source_requires_explicit_endpoint():
    with pytest.raises(
        ValueError,
        match="choosing start or end",
    ):
        bent_endpoint_intersection_3d(
            make_bent_member(),
            vertical_target(
                -40.0
            ),
            None,
        )


def test_bent_target_is_not_treated_as_a_chord():
    source = make_bent_member()

    with pytest.raises(
        ValueError,
        match="straight target",
    ):
        bent_endpoint_intersection_3d(
            source,
            source,
            "start",
        )
