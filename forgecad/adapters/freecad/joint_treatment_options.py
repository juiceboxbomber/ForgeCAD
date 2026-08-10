"""Treatment-option helpers for the ForgeCAD Joint Inspector."""

from dataclasses import dataclass
from itertools import combinations

from forgecad.fabrication.joint_treatment import (
    JointTreatmentMode,
)


@dataclass(frozen=True, slots=True)
class JointTreatmentOption:
    """One user-selectable persistent joint treatment."""

    label: str
    mode: JointTreatmentMode
    through_layout_ids: tuple[str, ...] = ()


def member_display_name(
    member_object,
):
    """Return a readable generated-member name."""

    member_id = str(
        getattr(
            member_object,
            "MemberID",
            "",
        )
    ).strip()

    member_name = str(
        getattr(
            member_object,
            "MemberName",
            "",
        )
    ).strip()

    if member_id and member_name:
        return (
            f"{member_id} - "
            f"{member_name}"
        )

    if member_id:
        return member_id

    return "Member"


def member_layout_id(
    member_object,
):
    """Return the persistent source layout ID for a member."""

    return str(
        getattr(
            member_object,
            "SourceLayoutID",
            "",
        )
    ).strip()


def member_has_persistent_identity(
    member_object,
):
    """Return True when a member has a persistent layout ID."""

    return bool(
        member_layout_id(
            member_object
        )
    )


def automatic_treatment_option():
    """Return the default automatic treatment option."""

    return JointTreatmentOption(
        label="Automatic",
        mode=JointTreatmentMode.AUTO,
    )


def member_through_option(
    member_object,
):
    """Return a single-member-through option."""

    layout_id = (
        member_layout_id(
            member_object
        )
    )

    if not layout_id:
        raise ValueError(
            "Member does not have a persistent "
            "SourceLayoutID."
        )

    return JointTreatmentOption(
        label=(
            f"{member_display_name(member_object)} "
            f"Through"
        ),
        mode=(
            JointTreatmentMode.MEMBER_THROUGH
        ),
        through_layout_ids=(
            layout_id,
        ),
    )


def through_pair_option(
    first_member_object,
    second_member_object,
):
    """Return an explicit two-member through-pair option."""

    first_layout_id = (
        member_layout_id(
            first_member_object
        )
    )

    second_layout_id = (
        member_layout_id(
            second_member_object
        )
    )

    if (
        not first_layout_id
        or not second_layout_id
    ):
        raise ValueError(
            "Through-pair members must have persistent "
            "SourceLayoutID values."
        )

    return JointTreatmentOption(
        label=(
            f"{member_display_name(first_member_object)} + "
            f"{member_display_name(second_member_object)} "
            f"Through Pair"
        ),
        mode=(
            JointTreatmentMode.THROUGH_PAIR
        ),
        through_layout_ids=(
            first_layout_id,
            second_layout_id,
        ),
    )


def treatment_options_for_members(
    member_objects,
):
    """
    Return treatment choices appropriate for connected members.

    Two-member joints receive:
        Automatic
        Member A Through
        Member B Through
        Both Mitered

    Three-or-more-member joints receive:
        Automatic
        each individual member through
        every possible two-member through pair
    """

    members = list(
        member_objects
    )

    options = [
        automatic_treatment_option()
    ]

    if len(members) < 2:
        return tuple(
            options
        )

    persistent_members = [
        member
        for member in members
        if member_has_persistent_identity(
            member
        )
    ]

    for member in persistent_members:
        options.append(
            member_through_option(
                member
            )
        )

    if len(members) == 2:
        options.append(
            JointTreatmentOption(
                label="Both Mitered",
                mode=(
                    JointTreatmentMode.BOTH_COPED
                ),
            )
        )

        return tuple(
            options
        )

    for (
        first_member,
        second_member,
    ) in combinations(
        persistent_members,
        2,
    ):
        options.append(
            through_pair_option(
                first_member,
                second_member,
            )
        )

    return tuple(
        options
    )


def option_matches_saved_treatment(
    option,
    mode,
    through_layout_ids,
):
    """Return True when an option matches stored treatment data."""

    mode_value = str(
        getattr(
            mode,
            "value",
            mode,
        )
    ).strip()

    saved_ids = tuple(
        str(layout_id).strip()
        for layout_id
        in through_layout_ids
        if str(layout_id).strip()
    )

    return (
        option.mode.value
        == mode_value
        and option.through_layout_ids
        == saved_ids
    )


def selected_option_index(
    options,
    saved_treatment,
):
    """
    Return the option index matching persistent treatment data.

    Automatic is returned when no valid saved option matches.
    """

    if not options:
        return -1

    if saved_treatment is None:
        return 0

    mode, through_layout_ids = (
        saved_treatment
    )

    for index, option in enumerate(
        options
    ):
        if option_matches_saved_treatment(
            option,
            mode,
            through_layout_ids,
        ):
            return index

    return 0
