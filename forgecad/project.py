"""ForgeCAD project configuration and ownership."""

from dataclasses import dataclass, field
from enum import Enum

from forgecad.fabrication import (
    Frame,
    Material,
    TubeLibrary,
)


class ApplicationType(str, Enum):
    """Supported project application categories."""

    GENERAL = "general"
    OFF_ROAD = "off_road"
    ROCK_CRAWLER = "rock_crawler"
    KART = "kart"
    FORMULA_SAE = "formula_sae"
    CUSTOM = "custom"


class DisplayUnits(str, Enum):
    """Units used to display dimensions to the user."""

    MILLIMETERS = "mm"
    INCHES = "in"


@dataclass(slots=True)
class Project:
    """Owns the configuration and structural model for one project."""

    name: str
    application: ApplicationType = ApplicationType.GENERAL
    display_units: DisplayUnits = DisplayUnits.MILLIMETERS
    tube_library: TubeLibrary = field(default_factory=TubeLibrary)
    default_material: Material | None = None
    frame: Frame = field(default_factory=Frame)

    def __post_init__(self) -> None:
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("Project name cannot be empty.")

        self.application = ApplicationType(self.application)
        self.display_units = DisplayUnits(self.display_units)

    @property
    def active_profile_name(self) -> str | None:
        """Return the active tube-profile name, if one exists."""

        return self.tube_library.active_name
    