"""Physical bent-tube path definitions for ForgeCAD."""

from dataclasses import dataclass

from .bend import Bend
from .material import Material
from .tube_profile import TubeProfile


@dataclass(frozen=True, slots=True)
class StraightRun:
    """One straight centerline section of a physical tube."""

    length_mm: float

    def __post_init__(self) -> None:
        length = float(
            self.length_mm
        )

        if length < 0.0:
            raise ValueError(
                "Straight-run length cannot be negative."
            )

        object.__setattr__(
            self,
            "length_mm",
            length,
        )


@dataclass(frozen=True, slots=True)
class BentTube:
    """
    One physical piece of tube containing straight runs and bends.

    A tube with N bends always has N + 1 straight runs. Straight-run
    lengths are measured between tangent points or between a tube end
    and its nearest tangent point.
    """

    straight_runs: tuple[StraightRun, ...]
    bends: tuple[Bend, ...]
    profile: TubeProfile
    material: Material

    def __post_init__(self) -> None:
        straight_runs = tuple(
            self.straight_runs
        )
        bends = tuple(
            self.bends
        )

        if len(
            straight_runs
        ) != len(
            bends
        ) + 1:
            raise ValueError(
                "A bent tube must have exactly one more straight run "
                "than bend."
            )

        if not straight_runs:
            raise ValueError(
                "A bent tube must contain at least one straight run."
            )

        if not all(
            isinstance(
                run,
                StraightRun,
            )
            for run in straight_runs
        ):
            raise TypeError(
                "Bent-tube straight runs must be StraightRun objects."
            )

        if not all(
            isinstance(
                bend,
                Bend,
            )
            for bend in bends
        ):
            raise TypeError(
                "Bent-tube bends must be Bend objects."
            )

        object.__setattr__(
            self,
            "straight_runs",
            straight_runs,
        )
        object.__setattr__(
            self,
            "bends",
            bends,
        )

    @property
    def bend_count(self) -> int:
        """Return the number of bends in the physical tube."""

        return len(
            self.bends
        )

    @property
    def straight_length(self) -> float:
        """Return total straight centerline length."""

        return sum(
            run.length_mm
            for run in self.straight_runs
        )

    @property
    def bend_length(self) -> float:
        """Return total developed centerline length through all bends."""

        return sum(
            bend.arc_length
            for bend in self.bends
        )

    @property
    def developed_length(self) -> float:
        """Return total required tube centerline length before bending."""

        return (
            self.straight_length
            + self.bend_length
        )

    @property
    def weight_kg(self) -> float:
        """Return estimated weight of the complete physical tube."""

        volume_m3 = (
            self.profile.cross_sectional_area
            * self.developed_length
            / 1_000_000_000.0
        )

        return (
            volume_m3
            * self.material.density
        )
