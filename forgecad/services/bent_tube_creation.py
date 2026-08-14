"""Bent-tube creation services."""

from dataclasses import dataclass

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)


@dataclass(frozen=True, slots=True)
class BendInput:
    """User-entered values for one bend."""

    angle_degrees: float
    centerline_radius: float
    rotation_degrees: float = 0.0


@dataclass(frozen=True, slots=True)
class BentTubeInput:
    """User-entered definition of one bent tube."""

    name: str
    run_lengths: tuple[float, ...]
    bends: tuple[BendInput, ...]

    def __post_init__(self) -> None:
        name = self.name.strip()

        if not name:
            raise ValueError(
                "Bent tube name cannot be empty."
            )

        object.__setattr__(
            self,
            "name",
            name,
        )

        if len(self.run_lengths) != len(self.bends) + 1:
            raise ValueError(
                "Bent tube requires exactly one more "
                "straight run than bends."
            )

        if any(
            length <= 0.0
            for length in self.run_lengths
        ):
            raise ValueError(
                "Straight run lengths must be positive."
            )


def create_bent_tube(
    definition: BentTubeInput,
    profile: TubeProfile,
    material: Material,
) -> BentTube:
    """Create a fabrication BentTube from user-entered values."""

    straight_runs = tuple(
        StraightRun(
            length
        )
        for length in definition.run_lengths
    )

    bends = tuple(
        Bend(
            angle_degrees=bend.angle_degrees,
            centerline_radius=bend.centerline_radius,
            rotation_degrees=bend.rotation_degrees,
        )
        for bend in definition.bends
    )

    return BentTube(
        straight_runs=straight_runs,
        bends=bends,
        profile=profile,
        material=material,
    )
