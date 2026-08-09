"""Joint definitions for ForgeCAD."""

from dataclasses import dataclass, field

from .member import Member
from .node import Node


@dataclass(slots=True)
class Joint:
    """Represents multiple frame members meeting at one node."""

    node: Node
    members: list[Member] = field(
        default_factory=list
    )

    def add_member(
        self,
        member: Member,
    ) -> None:
        """Add a connected member to the joint."""

        if member not in self.members:
            self.members.append(
                member
            )

    @property
    def member_count(self) -> int:
        """Return the number of members meeting at this joint."""

        return len(
            self.members
        )

    @property
    def is_simple(self) -> bool:
        """Return True for a two-member joint."""

        return (
            self.member_count == 2
        )

    @property
    def is_multi_member(self) -> bool:
        """Return True when three or more members meet."""

        return (
            self.member_count >= 3
        )
    