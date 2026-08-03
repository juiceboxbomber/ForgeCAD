import math

import pytest

from forgecad.fabrication.tube_profile import TubeProfile


def test_inside_diameter():
    profile = TubeProfile(44.45, 3.048)

    assert profile.inside_diameter_mm == pytest.approx(38.354)


def test_cross_section_area():
    profile = TubeProfile(44.45, 3.048)

    expected = (math.pi / 4) * (44.45**2 - 38.354**2)

    assert profile.cross_section_area_mm2 == pytest.approx(expected)


@pytest.mark.parametrize(
    "outside,wall",
    [
        (0, 1),
        (-1, 1),
        (40, 0),
        (40, -1),
        (40, 20),
        (40, 25),
    ],
)
def test_invalid_dimensions(outside, wall):
    with pytest.raises(ValueError):
        TubeProfile(outside, wall)
        