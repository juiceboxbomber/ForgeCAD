from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Material:
    """Represents engineering properties of a material.

    Density is stored in kg/mm³.
    Strength values are stored in MPa.
    """

    name: str
    density: float
    yield_strength: float
    ultimate_strength: float
    elastic_modulus: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Material name cannot be empty.")

        if self.density <= 0:
            raise ValueError("Density must be greater than zero.")

        if self.yield_strength <= 0:
            raise ValueError(
                "Yield strength must be greater than zero."
            )

        if self.ultimate_strength <= 0:
            raise ValueError(
                "Ultimate strength must be greater than zero."
            )

        if self.elastic_modulus <= 0:
            raise ValueError(
                "Elastic modulus must be greater than zero."
            )

        if self.ultimate_strength < self.yield_strength:
            raise ValueError(
                "Ultimate strength cannot be less than yield strength."
            )
        