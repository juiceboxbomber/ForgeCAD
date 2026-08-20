"""Project-module definitions for ForgeCAD workflows."""

from dataclasses import dataclass

from forgecad.project import ProjectType


@dataclass(frozen=True, slots=True)
class WorkspaceDefaults:
    """Default 2D workspace settings for a project module."""

    width_mm: float
    height_mm: float
    major_grid_mm: float
    minor_grid_mm: float

    def __post_init__(self) -> None:
        if self.width_mm <= 0:
            raise ValueError(
                "Workspace width must be greater than zero."
            )

        if self.height_mm <= 0:
            raise ValueError(
                "Workspace height must be greater than zero."
            )

        if self.major_grid_mm <= 0:
            raise ValueError(
                "Major grid spacing must be greater than zero."
            )

        if self.minor_grid_mm <= 0:
            raise ValueError(
                "Minor grid spacing must be greater than zero."
            )

        if self.minor_grid_mm > self.major_grid_mm:
            raise ValueError(
                "Minor grid spacing cannot exceed major grid spacing."
            )


@dataclass(frozen=True, slots=True)
class ProjectModuleDefinition:
    """Describe one ForgeCAD project workflow module."""

    project_type: ProjectType
    display_name: str
    workflow_stages: tuple[str, ...]
    workspace: WorkspaceDefaults

    def __post_init__(self) -> None:
        if not self.display_name.strip():
            raise ValueError(
                "Project module display name cannot be empty."
            )

        if not self.workflow_stages:
            raise ValueError(
                "Project module requires at least one workflow stage."
            )

        if any(
            not stage.strip()
            for stage in self.workflow_stages
        ):
            raise ValueError(
                "Workflow stage names cannot be empty."
            )


GENERAL_FABRICATION_MODULE = ProjectModuleDefinition(
    project_type=ProjectType.GENERAL_FABRICATION,
    display_name="General Fabrication",
    workflow_stages=(
        "Layout",
        "Members",
        "Joints",
        "Fabrication Review",
    ),
    workspace=WorkspaceDefaults(
        width_mm=3000.0,
        height_mm=2000.0,
        major_grid_mm=100.0,
        minor_grid_mm=25.0,
    ),
)


CHASSIS_MODULE = ProjectModuleDefinition(
    project_type=ProjectType.CHASSIS,
    display_name="Chassis",
    workflow_stages=(
        "Base Layout",
        "Crossmembers",
        "Uprights",
        "Upper Structure",
        "Joints",
        "Fabrication Review",
    ),
    workspace=WorkspaceDefaults(
        width_mm=4000.0,
        height_mm=2000.0,
        major_grid_mm=100.0,
        minor_grid_mm=25.0,
    ),
)


ROLL_CAGE_MODULE = ProjectModuleDefinition(
    project_type=ProjectType.ROLL_CAGE,
    display_name="Roll Cage",
    workflow_stages=(
        "Reference Geometry",
        "Main Hoop",
        "Front Structure",
        "Roof Structure",
        "Bracing",
        "Bends",
        "Joints",
        "Fabrication Review",
    ),
    workspace=WorkspaceDefaults(
        width_mm=2500.0,
        height_mm=2500.0,
        major_grid_mm=100.0,
        minor_grid_mm=25.0,
    ),
)


PROJECT_MODULES = {
    module.project_type: module
    for module in (
        GENERAL_FABRICATION_MODULE,
        CHASSIS_MODULE,
        ROLL_CAGE_MODULE,
    )
}


def project_module_for_type(
    project_type: ProjectType,
) -> ProjectModuleDefinition:
    """Return the project-module definition for a project type."""

    normalized_type = ProjectType(
        project_type
    )

    return PROJECT_MODULES[
        normalized_type
    ]
