"""Frame definitions for ForgeCAD."""

from dataclasses import dataclass, field

from .member import Member
from .node import Node


@dataclass(slots=True)
class Frame:
    """Represents an entire chassis frame."""

    nodes: list[Node] = field(default_factory=list)
    members: list[Member] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        """Add a node to the frame."""
        self.nodes.append(node)

    def add_member(self, member: Member) -> None:
        """Add a member to the frame."""
        self.members.append(member)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def member_count(self) -> int:
        return len(self.members)
    