"""Tests for ForgeCAD project creation services."""

from forgecad.fabrication import (
    BenderTooling,
)
from forgecad.services.project_service import (
    DEFAULT_PROFILE_NAME,
    create_default_bender_library,
    create_project,
)


def test_default_bender_library_starts_empty():
    library = create_default_bender_library()

    assert library.names == ()
    assert library.active_name is None
    assert library.active_tooling is None


def test_created_project_owns_empty_bender_library():
    project = create_project(
        "Bending Project"
    )

    assert project.bender_library.names == ()
    assert project.active_bender_tooling_name is None


def test_created_projects_do_not_share_bender_libraries():
    first = create_project(
        "First"
    )
    second = create_project(
        "Second"
    )

    first.bender_library.add(
        BenderTooling(
            name="Shop Die",
            centerline_radius_mm=120.0,
        )
    )

    assert first.active_bender_tooling_name == "Shop Die"
    assert second.active_bender_tooling_name is None


def test_project_creation_keeps_existing_default_tube_behavior():
    project = create_project(
        "Tube Defaults"
    )

    assert project.active_profile_name == DEFAULT_PROFILE_NAME
