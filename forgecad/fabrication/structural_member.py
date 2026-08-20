"""Shared structural-member types for ForgeCAD."""

from typing import TypeAlias

from .bent_member import BentMember
from .member import Member


StructuralMember: TypeAlias = (
    Member
    | BentMember
)


__all__ = [
    "StructuralMember",
]
