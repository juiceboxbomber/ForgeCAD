from __future__ import annotations

from dataclasses import dataclass, field

from forgecad.fabrication.member import Member
from forgecad.fabrication.node import Node


@dataclass
class Frame:
    """Represents a fabricated structure made from members and nodes."""

    name: str
    nodes: list[Node] = field(default_factory=list)
    members: list[Member] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Frame name cannot be empty.")

    def add_node(self, node: Node) -> None:
        """Add a node to the frame."""

        if node not in self.nodes:
            self.nodes.append(node)

    def add_member(self, member: Member) -> None:
        """Add a member to the frame."""

        self.members.append(member)

        self.add_node(member.start_node)
        self.add_node(member.end_node)

    @property
    def total_length(self) -> float:
        """Return total member length in millimeters."""

        return sum(
            member.length
            for member in self.members
        )
    