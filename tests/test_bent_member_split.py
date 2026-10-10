import pytest

from forgecad.fabrication import Bend, BentTube, Material, StraightRun, TubeProfile
from forgecad.geometry import Point3D
from forgecad.services.member_split import (
    bent_split_location,
    split_bent_tube,
)


def _material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def _profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def _tube():
    return BentTube(
        straight_runs=(
            StraightRun(500.0),
            StraightRun(750.0),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


def test_bent_split_location_resolves_first_straight_run():
    location = bent_split_location(
        _tube(),
        Point3D(250.0, 0.0, 0.0),
    )

    assert location.straight_run_index == 0
    assert location.fraction == pytest.approx(0.5)
    assert location.point == Point3D(250.0, 0.0, 0.0)


def test_bent_split_location_resolves_last_straight_run():
    location = bent_split_location(
        _tube(),
        Point3D(600.0, 475.0, 0.0),
    )

    assert location.straight_run_index == 1
    assert location.fraction == pytest.approx(0.5)
    assert location.point.x == pytest.approx(600.0)
    assert location.point.y == pytest.approx(475.0)
    assert location.point.z == pytest.approx(0.0)


def test_bent_split_location_rejects_point_on_bend_arc():
    with pytest.raises(ValueError, match="straight portion"):
        bent_split_location(
            _tube(),
            Point3D(570.710678, 29.289322, 0.0),
            tolerance=1e-3,
        )


def test_bent_split_location_rejects_bend_tangent():
    with pytest.raises(ValueError, match="inside a straight run"):
        bent_split_location(
            _tube(),
            Point3D(500.0, 0.0, 0.0),
        )


def test_split_bent_tube_on_first_run_preserves_remaining_bend_path():
    tube = _tube()

    first, second, location = split_bent_tube(
        tube,
        Point3D(
            250.0,
            0.0,
            0.0,
        ),
    )

    assert location.straight_run_index == 0

    assert first.bend_count == 0
    assert tuple(
        run.length_mm
        for run in first.straight_runs
    ) == pytest.approx(
        (
            250.0,
        )
    )

    assert second.bend_count == 1
    assert tuple(
        run.length_mm
        for run in second.straight_runs
    ) == pytest.approx(
        (
            250.0,
            750.0,
        )
    )

    assert second.bends == tube.bends


def test_split_bent_tube_on_last_run_preserves_leading_bend_path():
    tube = _tube()

    first, second, location = split_bent_tube(
        tube,
        Point3D(
            600.0,
            475.0,
            0.0,
        ),
    )

    assert location.straight_run_index == 1

    assert first.bend_count == 1
    assert tuple(
        run.length_mm
        for run in first.straight_runs
    ) == pytest.approx(
        (
            500.0,
            375.0,
        )
    )

    assert first.bends == tube.bends

    assert second.bend_count == 0
    assert tuple(
        run.length_mm
        for run in second.straight_runs
    ) == pytest.approx(
        (
            375.0,
        )
    )


def test_split_bent_tube_preserves_profile_and_material():
    tube = _tube()

    first, second, _ = split_bent_tube(
        tube,
        Point3D(
            250.0,
            0.0,
            0.0,
        ),
    )

    assert first.profile == tube.profile
    assert second.profile == tube.profile
    assert first.material == tube.material
    assert second.material == tube.material
