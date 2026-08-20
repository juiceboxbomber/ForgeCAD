"""3D vector mathematics for ForgeCAD."""

from dataclasses import dataclass
from math import cos, radians, sin, sqrt


@dataclass(frozen=True, slots=True)
class Vector3D:
    """Represents a 3D vector."""

    x: float
    y: float
    z: float

    @property
    def magnitude(self) -> float:
        return sqrt(
            self.x**2
            + self.y**2
            + self.z**2
        )

    def normalized(self) -> "Vector3D":
        """Return a unit-length copy of this vector."""

        mag = self.magnitude

        if mag == 0:
            raise ValueError(
                "Cannot normalize a zero-length vector."
            )

        return Vector3D(
            self.x / mag,
            self.y / mag,
            self.z / mag,
        )

    def dot(
        self,
        other: "Vector3D",
    ) -> float:
        """Return the scalar dot product."""

        return (
            self.x * other.x
            + self.y * other.y
            + self.z * other.z
        )

    def cross(
        self,
        other: "Vector3D",
    ) -> "Vector3D":
        """Return the right-handed vector cross product."""

        return Vector3D(
            self.y * other.z
            - self.z * other.y,
            self.z * other.x
            - self.x * other.z,
            self.x * other.y
            - self.y * other.x,
        )

    def scaled(
        self,
        factor: float,
    ) -> "Vector3D":
        """Return this vector multiplied by a scalar."""

        factor = float(
            factor
        )

        return Vector3D(
            self.x * factor,
            self.y * factor,
            self.z * factor,
        )

    def plus(
        self,
        other: "Vector3D",
    ) -> "Vector3D":
        """Return vector addition."""

        return Vector3D(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
        )

    def minus(
        self,
        other: "Vector3D",
    ) -> "Vector3D":
        """Return vector subtraction."""

        return Vector3D(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z,
        )

    def rotated_about(
        self,
        axis: "Vector3D",
        angle_degrees: float,
    ) -> "Vector3D":
        """
        Rotate this vector about an axis using Rodrigues' formula.

        Positive rotation follows the right-hand rule.
        """

        unit_axis = axis.normalized()
        angle = radians(
            float(
                angle_degrees
            )
        )

        cosine = cos(
            angle
        )
        sine = sin(
            angle
        )

        parallel = unit_axis.scaled(
            unit_axis.dot(
                self
            )
            * (
                1.0
                - cosine
            )
        )

        return (
            self.scaled(
                cosine
            )
            .plus(
                unit_axis.cross(
                    self
                ).scaled(
                    sine
                )
            )
            .plus(
                parallel
            )
        )
