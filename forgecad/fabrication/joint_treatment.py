"""Joint treatment definitions for ForgeCAD."""

from dataclasses import dataclass
from enum import Enum

from .joint import Joint
from .member import Member


class JointTreatmentMode(
    str,
    Enum,
):
    """Available fabrication treatments for a tube joint."""

    AUTO = "auto"

    MEMBER_THROUGH = (
        "member_through"
    )

    BOTH_COPED = (
        "both_coped"
    )

    THROUGH_PAIR = (
        "through_pair"
    )


@dataclass(
    frozen=True,
    slots=True,
)
class JointTreatment:
    """Describe the intended fabrication treatment at a joint."""

    joint: Joint

    mode: JointTreatmentMode = (
        JointTreatmentMode.AUTO
    )

    through_members: tuple[
        Member,
        ...,
    ] = ()

    def __post_init__(
        self,
    ) -> None:
        """Validate treatment configuration."""

        members = tuple(
            self.joint.members
        )

        for member in (
            self.through_members
        ):
            if member not in members:
                raise ValueError(
                    "A selected through member "
                    "must belong to the joint."
                )

        if (
            len(
                self.through_members
            )
            != len(
                {
                    id(member)
                    for member
                    in self.through_members
                }
            )
        ):
            raise ValueError(
                "Through members must be unique."
            )

        if (
            self.mode
            == JointTreatmentMode.AUTO
        ):
            if self.through_members:
                raise ValueError(
                    "Automatic treatment cannot "
                    "specify through members."
                )

            return

        if (
            self.mode
            == JointTreatmentMode.MEMBER_THROUGH
        ):
            if (
                len(
                    self.through_members
                )
                != 1
            ):
                raise ValueError(
                    "Member-through treatment requires "
                    "exactly one through member."
                )

            if (
                self.joint.member_count
                < 2
            ):
                raise ValueError(
                    "Member-through treatment requires "
                    "at least two connected members."
                )

            return

        if (
            self.mode
            == JointTreatmentMode.BOTH_COPED
        ):
            if self.through_members:
                if (
                    len(
                        self.through_members
                    )
                    != 2
                ):
                    raise ValueError(
                        "Both-mitered treatment requires "
                        "exactly two selected members."
                    )
            elif (
                self.joint.member_count
                != 2
            ):
                raise ValueError(
                    "Legacy both-mitered treatment without "
                    "member identity requires exactly two members."
                )

            return

        if (
            self.mode
            == JointTreatmentMode.THROUGH_PAIR
        ):
            if (
                len(
                    self.through_members
                )
                != 2
            ):
                raise ValueError(
                    "Through-pair treatment requires "
                    "exactly two through members."
                )

            if (
                self.joint.member_count
                < 2
            ):
                raise ValueError(
                    "Through-pair treatment requires "
                    "at least two connected members."
                )

            return

        raise ValueError(
            "Unsupported joint treatment mode."
        )

    @property
    def through_member_count(
        self,
    ) -> int:
        """Return the number of explicitly selected through members."""

        return len(
            self.through_members
        )

    @property
    def coped_members(
        self,
    ) -> tuple[
        Member,
        ...,
    ]:
        """
        Return members explicitly designated for coping.

        Automatic treatment has no explicit answer until
        ForgeCAD resolves it using joint geometry.
        """

        if (
            self.mode
            == JointTreatmentMode.AUTO
        ):
            return ()

        if (
            self.mode
            == JointTreatmentMode.BOTH_COPED
        ):
            if self.through_members:
                return tuple(
                    self.through_members
                )

            return tuple(
                self.joint.members
            )

        return tuple(
            member
            for member
            in self.joint.members
            if member
            not in self.through_members
        )

    @property
    def cope_member_count(
        self,
    ) -> int:
        """Return the number of explicitly coped members."""

        return len(
            self.coped_members
        )

    @property
    def is_automatic(
        self,
    ) -> bool:
        """Return True when ForgeCAD should choose the treatment."""

        return (
            self.mode
            == JointTreatmentMode.AUTO
        )

    @classmethod
    def automatic(
        cls,
        joint: Joint,
    ):
        """Create an automatic joint treatment."""

        return cls(
            joint=joint,
            mode=(
                JointTreatmentMode.AUTO
            ),
        )

    @classmethod
    def member_through(
        cls,
        joint: Joint,
        member: Member,
    ):
        """Create a treatment where one member continues through."""

        return cls(
            joint=joint,
            mode=(
                JointTreatmentMode.MEMBER_THROUGH
            ),
            through_members=(
                member,
            ),
        )

    @classmethod
    def both_coped(
        cls,
        joint: Joint,
        first_member: Member | None = None,
        second_member: Member | None = None,
    ):
        """
        Create the persistence-compatible Both Mitered treatment.

        Legacy two-member joints may omit the explicit pair. New saved
        treatments should provide both members so the miter survives when
        additional members are later connected at the same node.
        """

        if (
            (first_member is None)
            != (second_member is None)
        ):
            raise ValueError(
                "Both-mitered treatment must specify "
                "both selected members or neither."
            )

        selected_members = ()

        if first_member is not None:
            selected_members = (
                first_member,
                second_member,
            )

        return cls(
            joint=joint,
            mode=(
                JointTreatmentMode.BOTH_COPED
            ),
            through_members=(
                selected_members
            ),
        )

    @classmethod
    def through_pair(
        cls,
        joint: Joint,
        first_member: Member,
        second_member: Member,
    ):
        """Create a treatment with an explicit through pair."""

        return cls(
            joint=joint,
            mode=(
                JointTreatmentMode.THROUGH_PAIR
            ),
            through_members=(
                first_member,
                second_member,
            ),
        )
    