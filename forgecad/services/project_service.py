"""Project creation services for ForgeCAD."""

from forgecad import (
    ApplicationType,
    DisplayUnits,
    Project,
    ProjectType,
)
from forgecad.fabrication import (
    BenderLibrary,
    Material,
    TubeLibrary,
    TubeProfile,
)


DEFAULT_PROFILE_NAME = "1.750 x .120 DOM"


DEFAULT_DOM_TUBE_PROFILES = (
    ("0.750 x .049 DOM", 19.0500, 1.2446),
    ("0.750 x .065 DOM", 19.0500, 1.6510),
    ("0.750 x .083 DOM", 19.0500, 2.1082),
    ("1.000 x .049 DOM", 25.4000, 1.2446),
    ("1.000 x .065 DOM", 25.4000, 1.6510),
    ("1.000 x .083 DOM", 25.4000, 2.1082),
    ("1.000 x .095 DOM", 25.4000, 2.4130),
    ("1.000 x .120 DOM", 25.4000, 3.0480),
    ("1.250 x .065 DOM", 31.7500, 1.6510),
    ("1.250 x .083 DOM", 31.7500, 2.1082),
    ("1.250 x .095 DOM", 31.7500, 2.4130),
    ("1.250 x .120 DOM", 31.7500, 3.0480),
    ("1.500 x .065 DOM", 38.1000, 1.6510),
    ("1.500 x .083 DOM", 38.1000, 2.1082),
    ("1.500 x .095 DOM", 38.1000, 2.4130),
    ("1.500 x .120 DOM", 38.1000, 3.0480),
    ("1.500 x .134 DOM", 38.1000, 3.4036),
    ("1.625 x .083 DOM", 41.2750, 2.1082),
    ("1.625 x .095 DOM", 41.2750, 2.4130),
    ("1.625 x .120 DOM", 41.2750, 3.0480),
    ("1.750 x .083 DOM", 44.4500, 2.1082),
    ("1.750 x .095 DOM", 44.4500, 2.4130),
    ("1.750 x .120 DOM", 44.4500, 3.0480),
    ("1.750 x .134 DOM", 44.4500, 3.4036),
    ("2.000 x .095 DOM", 50.8000, 2.4130),
    ("2.000 x .120 DOM", 50.8000, 3.0480),
    ("2.000 x .134 DOM", 50.8000, 3.4036),
    ("2.000 x .188 DOM", 50.8000, 4.7752),
    ("2.250 x .120 DOM", 57.1500, 3.0480),
    ("2.250 x .134 DOM", 57.1500, 3.4036),
    ("2.250 x .188 DOM", 57.1500, 4.7752),
    ("2.500 x .120 DOM", 63.5000, 3.0480),
    ("2.500 x .188 DOM", 63.5000, 4.7752),
)


def create_default_material() -> Material:
    """Create the default tubing material."""

    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def create_default_tube_library() -> TubeLibrary:
    """Create the standard ForgeCAD DOM round-tube profile library."""

    library = TubeLibrary()

    for name, outside_diameter, wall_thickness in DEFAULT_DOM_TUBE_PROFILES:
        library.add(
            name,
            TubeProfile(
                outside_diameter=outside_diameter,
                wall_thickness=wall_thickness,
            ),
        )

    library.set_active(
        DEFAULT_PROFILE_NAME
    )

    return library



def create_default_bender_library() -> BenderLibrary:
    """
    Create an empty project bender library.

    ForgeCAD does not assume a die CLR or calibration because those
    values depend on the fabricator's actual bender and tooling.
    """

    return BenderLibrary()


def create_project(
    name: str,
    project_type: ProjectType = ProjectType.GENERAL_FABRICATION,
    application: ApplicationType = ApplicationType.GENERAL,
    display_units: DisplayUnits = DisplayUnits.MILLIMETERS,
    active_profile_name: str = DEFAULT_PROFILE_NAME,
) -> Project:
    """Create a configured ForgeCAD project."""

    tube_library = create_default_tube_library()
    tube_library.set_active(
        active_profile_name
    )

    return Project(
        name=name,
        project_type=project_type,
        application=application,
        display_units=display_units,
        tube_library=tube_library,
        bender_library=create_default_bender_library(),
        default_material=create_default_material(),
    )
