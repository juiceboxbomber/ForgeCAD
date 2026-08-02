from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Node:
    """Represents a connection point in a fabricated structure.

    Coordinates are stored internally in millimeters.
    """

    id: UUID
    x: float
    y: float
    z: float

    @classmethod
    def at(
        cls,
        x: float,
        y: float,
        z: float,
    ) -> Node:
        """Create a new node at a location."""

        return cls(
            id=uuid4(),
            x=x,
            y=y,
            z=z,
        )
    