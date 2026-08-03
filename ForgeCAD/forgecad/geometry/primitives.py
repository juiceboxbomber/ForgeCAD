from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point3D:
    """A 3D point expressed in millimeters."""

    x: float
    y: float
    z: float


@dataclass(frozen=True, slots=True)
class LineSegment:
    """A line segment between two 3D points."""

    start: Point3D
    end: Point3D

    @property
    def length(self) -> float:
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        dz = self.end.z - self.start.z

        return (dx**2 + dy**2 + dz**2) ** 0.5
    