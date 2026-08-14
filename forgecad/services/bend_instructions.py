"""Fabrication bend-instruction services for ForgeCAD."""

from dataclasses import dataclass
from forgecad.fabrication import (
    BendMarkReference,
    BentTube,
)
from forgecad.services.bend_schedule import (
    BendSchedule,
    build_bend_schedule,
)


@dataclass(frozen=True, slots=True)
class BendInstruction:
    """One shop-floor bend instruction for a physical tube."""

    bend_number: int
    mark_position_mm: float
    mark_reference: BendMarkReference
    angle_degrees: float
    centerline_radius_mm: float
    rotation_degrees: float


@dataclass(frozen=True, slots=True)
class BendInstructions:
    """Ordered fabrication instructions for one physical tube."""

    items: tuple[BendInstruction, ...]
    cut_length_mm: float

    @property
    def bend_count(self) -> int:
        """Return number of bend instructions."""

        return len(
            self.items
        )


def mark_position_for_schedule_item(
    item,
    reference: BendMarkReference,
) -> float:
    """Return developed mark position for one bend."""

    reference = BendMarkReference(
        reference
    )

    if reference == BendMarkReference.START_TANGENT:
        return item.start_position_mm

    if reference == BendMarkReference.CENTER_OF_BEND:
        return (
            item.start_position_mm
            + item.arc_length_mm / 2.0
        )

    raise ValueError(
        "Unsupported bend mark reference."
    )


def instructions_from_schedule(
    schedule: BendSchedule,
    mark_reference: BendMarkReference = (
        BendMarkReference.START_TANGENT
    ),
) -> BendInstructions:
    """Convert geometric bend schedule data into fabrication marks."""

    if not isinstance(
        schedule,
        BendSchedule,
    ):
        raise TypeError(
            "schedule must be a BendSchedule instance."
        )

    reference = BendMarkReference(
        mark_reference
    )

    items = tuple(
        BendInstruction(
            bend_number=item.bend_number,
            mark_position_mm=(
                mark_position_for_schedule_item(
                    item,
                    reference,
                )
            ),
            mark_reference=reference,
            angle_degrees=item.angle_degrees,
            centerline_radius_mm=(
                item.centerline_radius_mm
            ),
            rotation_degrees=(
                item.rotation_degrees
            ),
        )
        for item in schedule.items
    )

    return BendInstructions(
        items=items,
        cut_length_mm=(
            schedule.developed_length_mm
        ),
    )


def build_bend_instructions(
    tube: BentTube,
    mark_reference: BendMarkReference = (
        BendMarkReference.START_TANGENT
    ),
) -> BendInstructions:
    """Build shop-floor bend instructions for a physical tube."""

    return instructions_from_schedule(
        build_bend_schedule(
            tube
        ),
        mark_reference=mark_reference,
    )
