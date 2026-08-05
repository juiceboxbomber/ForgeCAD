"""Centerline layout definitions for ForgeCAD."""

from dataclasses import dataclass, field

from forgecad.geometry import Point3D


@dataclass(frozen=True, slots=True)
class LayoutLine:
    """Represents one centerline segment in a frame layout."""

    start: Point3D
    end: Point3D

    def __post_init__(self) -> None:
        if self.start == self.end:
            raise ValueError("A layout line must have a nonzero length.")

    @property
    def length(self) -> float:
        """Return the line length in millimeters."""

        return self.start.vector_to(self.end).magnitude


@dataclass(slots=True)
class FrameLayout:
    """Stores centerlines used to generate a structural frame."""

    lines: list[LayoutLine] = field(default_factory=list)

    def add_line(self, line: LayoutLine) -> None:
        """Add a centerline to the layout."""

        if line not in self.lines:
            self.lines.append(line)

    @property
    def line_count(self) -> int:
        """Return the number of layout lines."""

        return len(self.lines)

    @property
    def points(self) -> tuple[Point3D, ...]:
        """Return unique layout endpoints in insertion order."""

        points: list[Point3D] = []

        for line in self.lines:
            if line.start not in points:
                points.append(line.start)

            if line.end not in points:
                points.append(line.end)

        return tuple(points)
    