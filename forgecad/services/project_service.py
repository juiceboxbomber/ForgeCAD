"""Project creation services for ForgeCAD."""

from forgecad import (
    ApplicationType,
    DisplayUnits,
    Project,
    ProjectType,
)
from forgecad.fabrication import (
    Material,
    TubeLibrary,
    TubeProfile,
)


DEFAULT_PROFILE_NAME = "1.750 x .120 DOM"


def create_default_material() -> Material:
    """Create the default tubing material."""

    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def create_default_tube_library() -> TubeLibrary:
    """Create the starter tube-profile library."""

    library = TubeLibrary()

    library.add(
        "1.000 x .065 DOM",
        TubeProfile(
            outside_diameter=25.4,
            wall_thickness=1.651,
        ),
    )

    library.add(
        "1.250 x .095 DOM",
        TubeProfile(
            outside_diameter=31.75,
            wall_thickness=2.413,
        ),
    )

    library.add(
        DEFAULT_PROFILE_NAME,
        TubeProfile(
            outside_diameter=44.45,
            wall_thickness=3.048,
        ),
    )

    library.set_active(
        DEFAULT_PROFILE_NAME
    )

    return library


def create_project(
    name: str,
    project_type: ProjectType = (
        ProjectType.GENERAL_FABRICATION
    ),
    application: ApplicationType = ApplicationType.GENERAL,
    display_units: DisplayUnits = DisplayUnits.MILLIMETERS,
    active_profile_name: str = DEFAULT_PROFILE_NAME,
) -> Project:
    """Create a configured ForgeCAD project."""

    tube_library = (
        create_default_tube_library()
    )
    tube_library.set_active(
        active_profile_name
    )

    return Project(
        name=name,
        project_type=project_type,
        application=application,
        display_units=display_units,
        tube_library=tube_library,
        default_material=create_default_material(),
    )
