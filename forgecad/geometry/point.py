"""3D point geometry."""

from dataclasses import dataclass

from .vector import Vector3D


@dataclass(frozen=True, slots=True)
class Point3D:
    """Represents a point in 3D space."""

    x: float
    y: float
    z: float

    def vector_to(self, other: "Point3D") -> Vector3D:
        """Return the vector from this point to another point."""
        return Vector3D(
            other.x - self.x,
            other.y - self.y,
            other.z - self.z,
        )

    def translate(self, vector: Vector3D) -> "Point3D":
        """Return a translated copy of this point."""
        return Point3D(
            self.x + vector.x,
            self.y + vector.y,
            self.z + vector.z,
        )
    