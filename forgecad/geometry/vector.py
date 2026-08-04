"""3D vector mathematics for ForgeCAD."""

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True, slots=True)
class Vector3D:
    """Represents a 3D vector."""

    x: float
    y: float
    z: float

    @property
    def magnitude(self) -> float:
        return sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalized(self) -> "Vector3D":
        mag = self.magnitude

        if mag == 0:
            raise ValueError("Cannot normalize a zero-length vector.")

        return Vector3D(
            self.x / mag,
            self.y / mag,
            self.z / mag,
        )

    def dot(self, other: "Vector3D") -> float:
        return (
            self.x * other.x +
            self.y * other.y +
            self.z * other.z
        )
    