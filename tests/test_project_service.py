import pytest

from forgecad import ApplicationType, DisplayUnits
from forgecad.services import (
    DEFAULT_PROFILE_NAME,
    create_default_material,
    create_default_tube_library,
    create_project,
)


def test_create_default_material():
    material = create_default_material()

    assert material.name == "A513 Type 5 DOM"
    assert material.density == 7850.0
    assert material.yield_strength == 350.0


def test_create_default_tube_library():
    library = create_default_tube_library()

    assert library.names == (
        "1.000 x .065 DOM",
        "1.250 x .095 DOM",
        "1.750 x .120 DOM",
    )
    assert library.active_name == DEFAULT_PROFILE_NAME


def test_create_project():
    project = create_project(
        name="Crawler Chassis",
        application=ApplicationType.ROCK_CRAWLER,
        display_units=DisplayUnits.INCHES,
    )

    assert project.name == "Crawler Chassis"
    assert project.application is ApplicationType.ROCK_CRAWLER
    assert project.display_units is DisplayUnits.INCHES
    assert project.default_material is not None
    assert project.active_profile_name == DEFAULT_PROFILE_NAME


def test_select_active_profile_during_creation():
    project = create_project(
        name="Small Frame",
        active_profile_name="1.250 x .095 DOM",
    )

    assert project.active_profile_name == "1.250 x .095 DOM"
    assert project.tube_library.active_profile.outside_diameter == 31.75


def test_unknown_active_profile_is_rejected():
    with pytest.raises(KeyError):
        create_project(
            name="Invalid Project",
            active_profile_name="Missing Profile",
        )
        