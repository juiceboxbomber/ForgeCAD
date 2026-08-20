"""Tests for ForgeCAD project types."""

from forgecad import (
    ApplicationType,
    Project,
    ProjectType,
)
from forgecad.services import (
    create_project,
)


def test_project_defaults_to_general_fabrication():
    project = Project(
        name="Test Project"
    )

    assert (
        project.project_type
        == ProjectType.GENERAL_FABRICATION
    )


def test_project_accepts_chassis_type():
    project = Project(
        name="Chassis Project",
        project_type=ProjectType.CHASSIS,
    )

    assert (
        project.project_type
        == ProjectType.CHASSIS
    )


def test_project_accepts_roll_cage_type():
    project = Project(
        name="Cage Project",
        project_type=ProjectType.ROLL_CAGE,
    )

    assert (
        project.project_type
        == ProjectType.ROLL_CAGE
    )


def test_project_type_is_independent_of_application():
    project = create_project(
        name="Crawler Chassis",
        project_type=ProjectType.CHASSIS,
        application=ApplicationType.ROCK_CRAWLER,
    )

    assert (
        project.project_type
        == ProjectType.CHASSIS
    )
    assert (
        project.application
        == ApplicationType.ROCK_CRAWLER
    )
