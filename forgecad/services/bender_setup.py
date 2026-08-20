"""Apply tubing-bender tooling to ForgeCAD bend instructions."""

from dataclasses import dataclass

from forgecad.fabrication import (
    BenderTooling,
    BentTube,
)
from forgecad.services.bend_instructions import (
    BendInstruction,
    BendInstructions,
    build_bend_instructions,
)


@dataclass(frozen=True, slots=True)
class MachineBendInstruction:
    """One bend instruction adjusted for a specific bender setup."""

    bend_number: int
    mark_position_mm: float
    bend_angle_degrees: float
    centerline_radius_mm: float
    rotation_degrees: float
    tooling_name: str


@dataclass(frozen=True, slots=True)
class MachineBendInstructions:
    """Complete machine-specific bend instructions for one tube."""

    items: tuple[
        MachineBendInstruction,
        ...,
    ]

    cut_length_mm: float
    tooling_name: str

    @property
    def bend_count(self) -> int:
        """Return number of machine bend instructions."""

        return len(
            self.items
        )


def validate_tooling_for_tube(
    tube: BentTube,
    tooling: BenderTooling,
    radius_tolerance_mm: float = 0.001,
) -> None:
    """Ensure every bend in the tube matches the selected tooling CLR."""

    tolerance = float(
        radius_tolerance_mm
    )

    if tolerance < 0.0:
        raise ValueError(
            "Radius tolerance cannot be negative."
        )

    for bend in tube.bends:
        if abs(
            bend.centerline_radius
            - tooling.centerline_radius_mm
        ) > tolerance:
            raise ValueError(
                "Tube bend centerline radius does not match selected tooling."
            )


def machine_instruction_from_ideal(
    instruction: BendInstruction,
    tooling: BenderTooling,
) -> MachineBendInstruction:
    """Apply tooling calibration offsets to one ideal bend instruction."""

    return MachineBendInstruction(
        bend_number=instruction.bend_number,
        mark_position_mm=(
            instruction.mark_position_mm
            + tooling.mark_offset_mm
        ),
        bend_angle_degrees=(
            instruction.angle_degrees
            + tooling.angle_compensation_degrees
        ),
        centerline_radius_mm=(
            tooling.centerline_radius_mm
        ),
        rotation_degrees=(
            instruction.rotation_degrees
        ),
        tooling_name=(
            tooling.name
        ),
    )


def build_machine_bend_instructions(
    tube: BentTube,
    tooling: BenderTooling,
) -> MachineBendInstructions:
    """Build calibrated bend instructions for a specific bender setup."""

    if not isinstance(
        tube,
        BentTube,
    ):
        raise TypeError(
            "tube must be a BentTube instance."
        )

    if not isinstance(
        tooling,
        BenderTooling,
    ):
        raise TypeError(
            "tooling must be a BenderTooling instance."
        )

    validate_tooling_for_tube(
        tube,
        tooling,
    )

    ideal = build_bend_instructions(
        tube,
        mark_reference=(
            tooling.mark_reference
        ),
    )

    return MachineBendInstructions(
        items=tuple(
            machine_instruction_from_ideal(
                instruction,
                tooling,
            )
            for instruction
            in ideal.items
        ),
        cut_length_mm=(
            ideal.cut_length_mm
        ),
        tooling_name=(
            tooling.name
        ),
    )
