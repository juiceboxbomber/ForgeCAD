"""Shop-ready bend report services for ForgeCAD."""

from dataclasses import dataclass

from forgecad.fabrication import (
    BenderTooling,
    BentTube,
)
from forgecad.services.bend_instructions import (
    build_bend_instructions,
)
from forgecad.services.bender_setup import (
    build_machine_bend_instructions,
)


@dataclass(frozen=True, slots=True)
class BendReportRow:
    """One shop-ready bend instruction row."""

    bend_number: int
    mark_position_mm: float
    bend_angle_degrees: float
    centerline_radius_mm: float
    rotation_degrees: float


@dataclass(frozen=True, slots=True)
class BendReport:
    """Shop-ready bend information for one physical tube."""

    tooling_name: str | None
    cut_length_mm: float
    rows: tuple[
        BendReportRow,
        ...,
    ]

    @property
    def bend_count(self) -> int:
        return len(
            self.rows
        )


def build_bend_report(
    tube: BentTube,
    tooling: BenderTooling | None = None,
) -> BendReport:
    """Build shop-ready bend information."""

    if tooling is None:
        instructions = build_bend_instructions(
            tube
        )

        rows = tuple(
            BendReportRow(
                bend_number=item.bend_number,
                mark_position_mm=item.mark_position_mm,
                bend_angle_degrees=item.angle_degrees,
                centerline_radius_mm=(
                    item.centerline_radius_mm
                ),
                rotation_degrees=(
                    item.rotation_degrees
                ),
            )
            for item in instructions.items
        )

        return BendReport(
            tooling_name=None,
            cut_length_mm=(
                instructions.cut_length_mm
            ),
            rows=rows,
        )

    instructions = (
        build_machine_bend_instructions(
            tube,
            tooling,
        )
    )

    rows = tuple(
        BendReportRow(
            bend_number=item.bend_number,
            mark_position_mm=item.mark_position_mm,
            bend_angle_degrees=(
                item.bend_angle_degrees
            ),
            centerline_radius_mm=(
                item.centerline_radius_mm
            ),
            rotation_degrees=(
                item.rotation_degrees
            ),
        )
        for item in instructions.items
    )

    return BendReport(
        tooling_name=(
            instructions.tooling_name
        ),
        cut_length_mm=(
            instructions.cut_length_mm
        ),
        rows=rows,
    )
