"""Bend-schedule services for ForgeCAD physical tubes."""

from dataclasses import dataclass

from forgecad.fabrication import (
    BentTube,
)


@dataclass(frozen=True, slots=True)
class BendScheduleItem:
    """One ordered bend instruction along a developed tube."""

    bend_number: int
    start_position_mm: float
    angle_degrees: float
    centerline_radius_mm: float
    rotation_degrees: float
    arc_length_mm: float


@dataclass(frozen=True, slots=True)
class BendSchedule:
    """Ordered fabrication bend instructions for one physical tube."""

    items: tuple[BendScheduleItem, ...]
    developed_length_mm: float

    @property
    def bend_count(self) -> int:
        """Return number of scheduled bends."""

        return len(
            self.items
        )


def build_bend_schedule(
    tube: BentTube,
) -> BendSchedule:
    """
    Build bend instructions measured from the tube start.

    Each start position is the developed centerline distance from the
    beginning of the tube to the start tangent of that bend.
    """

    if not isinstance(
        tube,
        BentTube,
    ):
        raise TypeError(
            "tube must be a BentTube instance."
        )

    items = []
    developed_position = 0.0

    for index, bend in enumerate(
        tube.bends,
        start=1,
    ):
        preceding_run = (
            tube.straight_runs[
                index - 1
            ]
        )

        developed_position += (
            preceding_run.length_mm
        )

        items.append(
            BendScheduleItem(
                bend_number=index,
                start_position_mm=(
                    developed_position
                ),
                angle_degrees=(
                    bend.angle_degrees
                ),
                centerline_radius_mm=(
                    bend.centerline_radius
                ),
                rotation_degrees=(
                    bend.rotation_degrees
                ),
                arc_length_mm=(
                    bend.arc_length
                ),
            )
        )

        developed_position += (
            bend.arc_length
        )

    return BendSchedule(
        items=tuple(
            items
        ),
        developed_length_mm=(
            tube.developed_length
        ),
    )
