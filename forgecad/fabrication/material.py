"""Material definitions for ForgeCAD."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Material:
    """Represents a material used to manufacture tubing."""

    name: str
    density: float          # kg/m³
    yield_strength: float   # MPa

    def __post_init__(self) -> None:
        if self.density <= 0:
            raise ValueError("Density must be greater than zero.")

        if self.yield_strength <= 0:
            raise ValueError("Yield strength must be greater than zero.")
        