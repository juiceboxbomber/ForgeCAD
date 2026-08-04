import math
import pytest

from forgecad.fabrication import TubeProfile


def test_inside_diameter():
    tube = TubeProfile(
        outside_diameter=31.75,
        wall_thickness=2.0,
    )

    assert tube.inside_diameter == pytest.approx(27.75)


def test_cross_sectional_area():
    tube = TubeProfile(31.75, 2.0)

    expected = (math.pi / 4) * (31.75**2 - 27.75**2)

    assert tube.cross_sectional_area == pytest.approx(expected)


def test_area_moment_of_inertia():
    tube = TubeProfile(31.75, 2.0)

    expected = (math.pi / 64) * (31.75**4 - 27.75**4)

    assert tube.area_moment_of_inertia == pytest.approx(expected)


def test_invalid_wall_thickness():
    with pytest.raises(ValueError):
        TubeProfile(
            outside_diameter=25.0,
            wall_thickness=13.0,
        )
        