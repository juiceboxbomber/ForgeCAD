import pytest

from forgecad.services.project_service import (
    DEFAULT_DOM_TUBE_PROFILES,
    DEFAULT_PROFILE_NAME,
    create_default_tube_library,
)


EXPECTED_NAMES = (
    "0.750 x .049 DOM",
    "0.750 x .065 DOM",
    "0.750 x .083 DOM",
    "1.000 x .049 DOM",
    "1.000 x .065 DOM",
    "1.000 x .083 DOM",
    "1.000 x .095 DOM",
    "1.000 x .120 DOM",
    "1.250 x .065 DOM",
    "1.250 x .083 DOM",
    "1.250 x .095 DOM",
    "1.250 x .120 DOM",
    "1.500 x .065 DOM",
    "1.500 x .083 DOM",
    "1.500 x .095 DOM",
    "1.500 x .120 DOM",
    "1.500 x .134 DOM",
    "1.625 x .083 DOM",
    "1.625 x .095 DOM",
    "1.625 x .120 DOM",
    "1.750 x .083 DOM",
    "1.750 x .095 DOM",
    "1.750 x .120 DOM",
    "1.750 x .134 DOM",
    "2.000 x .095 DOM",
    "2.000 x .120 DOM",
    "2.000 x .134 DOM",
    "2.000 x .188 DOM",
    "2.250 x .120 DOM",
    "2.250 x .134 DOM",
    "2.250 x .188 DOM",
    "2.500 x .120 DOM",
    "2.500 x .188 DOM",
)


def test_default_dom_library_contains_common_sizes():
    library = create_default_tube_library()
    assert library.names == EXPECTED_NAMES


def test_default_dom_library_has_no_duplicate_names():
    names = tuple(name for name, _, _ in DEFAULT_DOM_TUBE_PROFILES)
    assert len(names) == len(set(names))


def test_default_dom_library_keeps_existing_default():
    library = create_default_tube_library()
    assert library.active_name == DEFAULT_PROFILE_NAME
    assert DEFAULT_PROFILE_NAME == "1.750 x .120 DOM"


@pytest.mark.parametrize(
    ("name", "outside_diameter", "wall_thickness"),
    (
        ("0.750 x .049 DOM", 19.05, 1.2446),
        ("1.500 x .120 DOM", 38.10, 3.0480),
        ("1.625 x .095 DOM", 41.275, 2.4130),
        ("1.750 x .120 DOM", 44.45, 3.0480),
        ("2.000 x .188 DOM", 50.80, 4.7752),
        ("2.500 x .188 DOM", 63.50, 4.7752),
    ),
)
def test_common_dom_dimensions_are_metric_conversions(
    name,
    outside_diameter,
    wall_thickness,
):
    profile = create_default_tube_library().get(name)
    assert profile.outside_diameter == pytest.approx(outside_diameter)
    assert profile.wall_thickness == pytest.approx(wall_thickness)
