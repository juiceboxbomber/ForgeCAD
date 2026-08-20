"""Tubing-bender tooling library domain model for ForgeCAD."""

from dataclasses import dataclass, field

from .bender_tooling import BenderTooling


@dataclass(slots=True)
class BenderLibrary:
    """Named collection of tubing-bender tooling definitions."""

    _tooling: dict[str, BenderTooling] = field(default_factory=dict)
    _active_name: str | None = None

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._tooling.keys())

    @property
    def active_name(self) -> str | None:
        return self._active_name

    @property
    def active_tooling(self) -> BenderTooling | None:
        if self._active_name is None:
            return None
        return self._tooling[self._active_name]

    def add(self, tooling: BenderTooling) -> None:
        if not isinstance(tooling, BenderTooling):
            raise TypeError(
                "tooling must be a BenderTooling instance."
            )

        if tooling.name in self._tooling:
            raise ValueError(
                f"Bender tooling '{tooling.name}' already exists."
            )

        self._tooling[tooling.name] = tooling

        if self._active_name is None:
            self._active_name = tooling.name

    def get(self, name: str) -> BenderTooling:
        normalized_name = name.strip()

        if normalized_name not in self._tooling:
            raise KeyError(normalized_name)

        return self._tooling[normalized_name]

    def set_active(self, name: str) -> None:
        normalized_name = name.strip()

        if normalized_name not in self._tooling:
            raise KeyError(normalized_name)

        self._active_name = normalized_name

    def remove(self, name: str) -> BenderTooling:
        normalized_name = name.strip()

        if normalized_name not in self._tooling:
            raise KeyError(normalized_name)

        removed = self._tooling.pop(normalized_name)

        if self._active_name == normalized_name:
            self._active_name = next(iter(self._tooling), None)

        return removed

    def compatible_tooling(
        self,
        centerline_radius_mm: float,
        tolerance_mm: float = 0.001,
    ) -> tuple[BenderTooling, ...]:
        radius = float(centerline_radius_mm)
        tolerance = float(tolerance_mm)

        if radius <= 0.0:
            raise ValueError(
                "Centerline radius must be greater than zero."
            )

        if tolerance < 0.0:
            raise ValueError(
                "Tolerance cannot be negative."
            )

        return tuple(
            tooling
            for tooling in self._tooling.values()
            if abs(tooling.centerline_radius_mm - radius) <= tolerance
        )
