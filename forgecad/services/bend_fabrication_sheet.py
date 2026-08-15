"""Printable fabrication-sheet data for ForgeCAD bent tubes."""

from dataclasses import dataclass

from forgecad.fabrication import (
    BenderTooling,
    BentTube,
)
from forgecad.services.bend_path_diagram import (
    BendPathDiagram,
    build_bend_path_diagram,
)
from forgecad.services.bend_report import (
    BendReportRow,
    build_bend_report,
)
from forgecad.services.bent_tube_path import (
    build_bent_tube_centerline,
)


@dataclass(frozen=True, slots=True)
class BendFabricationSheet:
    """Complete printable fabrication data for one bent tube."""

    tube_name: str
    material_name: str
    outside_diameter_mm: float
    wall_thickness_mm: float
    inside_diameter_mm: float
    tooling_name: str | None
    cut_length_mm: float
    rows: tuple[BendReportRow, ...]
    diagram: BendPathDiagram | None = None

    @property
    def bend_count(self) -> int:
        """Return number of bends on the fabrication sheet."""
        return len(self.rows)


def build_bend_fabrication_sheet(
    tube: BentTube,
    tube_name: str,
    tooling: BenderTooling | None = None,
) -> BendFabricationSheet:
    """Build printable fabrication-sheet data from one bent tube."""

    if not isinstance(tube, BentTube):
        raise TypeError("tube must be a BentTube instance.")

    name = str(tube_name).strip()
    if not name:
        raise ValueError("Tube name cannot be empty.")

    report = build_bend_report(tube, tooling)
    centerline = build_bent_tube_centerline(tube)
    diagram = build_bend_path_diagram(centerline)

    return BendFabricationSheet(
        tube_name=name,
        material_name=tube.material.name,
        outside_diameter_mm=tube.profile.outside_diameter,
        wall_thickness_mm=tube.profile.wall_thickness,
        inside_diameter_mm=tube.profile.inside_diameter,
        tooling_name=report.tooling_name,
        cut_length_mm=report.cut_length_mm,
        rows=report.rows,
        diagram=diagram,
    )
