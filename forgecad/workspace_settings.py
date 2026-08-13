"""Editable ForgeCAD workspace settings."""

from dataclasses import dataclass

from forgecad.project_modules import (
    WorkspaceDefaults,
)


@dataclass(frozen=True, slots=True)
class WorkspaceSettings:
    """Per-project workspace configuration."""

    width_mm: float
    height_mm: float
    major_grid_mm: float
    minor_grid_mm: float
    grid_visible: bool = True
    snap_enabled: bool = True

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

    @classmethod
    def from_defaults(
        cls,
        defaults: WorkspaceDefaults,
    ) -> "WorkspaceSettings":
        """Create editable settings from project-module defaults."""

        return cls(
            width_mm=defaults.width_mm,
            height_mm=defaults.height_mm,
            major_grid_mm=defaults.major_grid_mm,
            minor_grid_mm=defaults.minor_grid_mm,
            grid_visible=True,
            snap_enabled=True,
        )
