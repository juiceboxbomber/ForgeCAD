import pytest

from forgecad import ApplicationType, DisplayUnits, Project
from forgecad.fabrication import Material, TubeProfile


def test_project_defaults():
    project = Project("My Chassis")

    assert project.name == "My Chassis"
    assert project.application is ApplicationType.GENERAL
    assert project.display_units is DisplayUnits.MILLIMETERS
    assert project.frame.node_count == 0
    assert project.frame.member_count == 0


def test_project_application_selection():
    project = Project(
        name="Crawler",
        application=ApplicationType.ROCK_CRAWLER,
    )

    assert project.application is ApplicationType.ROCK_CRAWLER


def test_project_display_units_do_not_change_internal_units():
    project = Project(
        name="Imperial Display",
        display_units=DisplayUnits.INCHES,
    )

    assert project.display_units is DisplayUnits.INCHES


def test_project_owns_tube_library():
    project = Project("Tube Test")
    profile = TubeProfile(44.45, 3.048)

    project.tube_library.add("1.750 x .120 DOM", profile)

    assert project.active_profile_name == "1.750 x .120 DOM"
    assert project.tube_library.active_profile is profile


def test_project_accepts_default_material():
    steel = Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )

    project = Project(
        name="Steel Frame",
        default_material=steel,
    )

    assert project.default_material is steel


@pytest.mark.parametrize("name", ["", "   ", "\t"])
def test_project_name_cannot_be_empty(name):
    with pytest.raises(ValueError):
        Project(name)

def test_project_converts_string_values_to_enums():
    project = Project(
        name="Qt Project",
        application="general",
        display_units="mm",
    )

    assert project.application is ApplicationType.GENERAL
    assert project.display_units is DisplayUnits.MILLIMETERS
            