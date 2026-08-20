"""Treatment-option helpers for the ForgeCAD Joint Inspector."""

from dataclasses import dataclass
from itertools import combinations
from math import acos, degrees, sqrt

from forgecad.fabrication.joint_treatment import (
    JointTreatmentMode,
)


DEFAULT_RIGHT_ANGLE_TOLERANCE_DEGREES = 3.0


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


def point_key(
    point,
    precision=6,
):
    """Return a stable coordinate key for a FreeCAD-like point."""

    return (
        round(
            float(point.x),
            precision,
        ),
        round(
            float(point.y),
            precision,
        ),
        round(
            float(point.z),
            precision,
        ),
    )


def vector_components(
    start,
    end,
):
    """Return XYZ vector components from start to end."""

    return (
        float(
            end.x - start.x
        ),
        float(
            end.y - start.y
        ),
        float(
            end.z - start.z
        ),
    )


def vector_length(
    vector,
):
    """Return vector magnitude."""

    return sqrt(
        vector[0] * vector[0]
        + vector[1] * vector[1]
        + vector[2] * vector[2]
    )


def point_on_member_interior(
    point,
    member,
    tolerance=1e-6,
):
    """Return True when a point lies strictly inside a member segment."""

    if (
        not hasattr(member, "StartPoint")
        or not hasattr(member, "EndPoint")
    ):
        return False

    start = member.StartPoint
    end = member.EndPoint

    segment = vector_components(
        start,
        end,
    )

    to_point = vector_components(
        start,
        point,
    )

    length_squared = (
        segment[0] * segment[0]
        + segment[1] * segment[1]
        + segment[2] * segment[2]
    )

    if length_squared <= 1e-12:
        return False

    parameter = (
        to_point[0] * segment[0]
        + to_point[1] * segment[1]
        + to_point[2] * segment[2]
    ) / length_squared

    if (
        parameter <= tolerance
        or parameter >= 1.0 - tolerance
    ):
        return False

    nearest_x = (
        float(start.x)
        + parameter * segment[0]
    )
    nearest_y = (
        float(start.y)
        + parameter * segment[1]
    )
    nearest_z = (
        float(start.z)
        + parameter * segment[2]
    )

    dx = float(point.x) - nearest_x
    dy = float(point.y) - nearest_y
    dz = float(point.z) - nearest_z

    distance_squared = (
        dx * dx
        + dy * dy
        + dz * dz
    )

    return (
        distance_squared
        <= tolerance * tolerance
    )


def continuous_member_for_two_member_joint(
    first_member,
    second_member,
):
    """
    Return the continuous member when the other member terminates
    on its interior.
    """

    for point in (
        second_member.StartPoint,
        second_member.EndPoint,
    ):
        if point_on_member_interior(
            point,
            first_member,
        ):
            return first_member

    for point in (
        first_member.StartPoint,
        first_member.EndPoint,
    ):
        if point_on_member_interior(
            point,
            second_member,
        ):
            return second_member

    return None


def continuous_members_for_multi_member_joint(
    member_objects,
):
    """
    Return members whose interior contains an endpoint of another member.

    This identifies the natural continuous tube in a branch joint without
    guessing when the topology is ambiguous.
    """

    members = list(member_objects)
    continuous = []

    for candidate in members:
        found_branch_endpoint = False

        for other_member in members:
            if other_member is candidate:
                continue

            for point in (
                other_member.StartPoint,
                other_member.EndPoint,
            ):
                if point_on_member_interior(
                    point,
                    candidate,
                ):
                    found_branch_endpoint = True
                    break

            if found_branch_endpoint:
                break

        if found_branch_endpoint:
            continuous.append(candidate)

    return tuple(continuous)


def common_member_point(
    first_member,
    second_member,
):
    """Return the common endpoint of two generated members."""

    first_points = (
        first_member.StartPoint,
        first_member.EndPoint,
    )

    second_points = (
        second_member.StartPoint,
        second_member.EndPoint,
    )

    for first_point in first_points:
        first_key = point_key(
            first_point
        )

        for second_point in second_points:
            if (
                point_key(
                    second_point
                )
                == first_key
            ):
                return first_point

    return None


def member_other_point(
    member,
    joint_point,
):
    """Return the endpoint of a member away from the joint."""

    joint_key = point_key(
        joint_point
    )

    if (
        point_key(
            member.StartPoint
        )
        == joint_key
    ):
        return member.EndPoint

    if (
        point_key(
            member.EndPoint
        )
        == joint_key
    ):
        return member.StartPoint

    raise ValueError(
        "Member does not touch the supplied joint point."
    )


def two_member_angle_degrees(
    first_member,
    second_member,
):
    """
    Return the smaller angle between two connected members.

    None is returned when the objects do not contain usable
    generated-member geometry.
    """

    required_properties = (
        "StartPoint",
        "EndPoint",
    )

    for member in (
        first_member,
        second_member,
    ):
        if not all(
            hasattr(
                member,
                property_name,
            )
            for property_name
            in required_properties
        ):
            return None

    joint_point = common_member_point(
        first_member,
        second_member,
    )

    if joint_point is None:
        return None

    try:
        first_other = member_other_point(
            first_member,
            joint_point,
        )

        second_other = member_other_point(
            second_member,
            joint_point,
        )

    except ValueError:
        return None

    first_vector = vector_components(
        joint_point,
        first_other,
    )

    second_vector = vector_components(
        joint_point,
        second_other,
    )

    first_length = vector_length(
        first_vector
    )

    second_length = vector_length(
        second_vector
    )

    if (
        first_length <= 1e-12
        or second_length <= 1e-12
    ):
        return None

    cosine = (
        (
            first_vector[0]
            * second_vector[0]
            + first_vector[1]
            * second_vector[1]
            + first_vector[2]
            * second_vector[2]
        )
        / (
            first_length
            * second_length
        )
    )

    cosine = max(
        -1.0,
        min(
            1.0,
            cosine,
        ),
    )

    angle = degrees(
        acos(
            cosine
        )
    )

    return min(
        angle,
        180.0 - angle,
    )


def is_right_angle_corner(
    first_member,
    second_member,
    tolerance_degrees=(
        DEFAULT_RIGHT_ANGLE_TOLERANCE_DEGREES
    ),
):
    """Return True when a two-member corner is approximately 90°."""

    angle = (
        two_member_angle_degrees(
            first_member,
            second_member,
        )
    )

    if angle is None:
        return False

    return (
        abs(
            angle - 90.0
        )
        <= float(
            tolerance_degrees
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


def both_mitered_option():
    """Return the two-member shared-miter option."""

    return JointTreatmentOption(
        label="Both Mitered",
        mode=(
            JointTreatmentMode.BOTH_COPED
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
    right_angle_tolerance_degrees=(
        DEFAULT_RIGHT_ANGLE_TOLERANCE_DEGREES
    ),
):
    """
    Return treatment choices appropriate for connected members.

    Bent structural members currently participate in frame/joint
    analysis, but fabrication treatment generation for bent-member
    ends is intentionally deferred.

    When any connected member is a bent-tube FreeCAD object, return
    only the safe Automatic option for now.
    """

    members = list(
        member_objects
    )

    options = [
        automatic_treatment_option()
    ]

    if len(
        members
    ) < 2:
        return tuple(
            options
        )

    # ---------------------------------------------------------
    # Bent-member protection
    # ---------------------------------------------------------
    #
    # Straight-member treatment logic below assumes every
    # FreeCAD member object has both StartPoint and EndPoint.
    #
    # Parametric bent tubes have StartPoint plus solved curved
    # geometry, so they must not enter the straight miter/cope
    # treatment path yet.
    #
    # Bent members can still:
    #   - participate in joint detection
    #   - participate in angle analysis
    #   - participate in joint classification
    #
    # Their fabrication treatments will be implemented later.
    # ---------------------------------------------------------

    has_bent_member = any(
        not hasattr(
            member,
            "EndPoint",
        )
        for member in members
    )

    if has_bent_member:
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

    # ---------------------------------------------------------
    # Two-member corner
    # ---------------------------------------------------------

    if len(
        members
    ) == 2:
        first_member = (
            members[
                0
            ]
        )

        second_member = (
            members[
                1
            ]
        )

        continuous_member = (
            continuous_member_for_two_member_joint(
                first_member,
                second_member,
            )
        )

        if continuous_member is not None:
            if member_has_persistent_identity(
                continuous_member
            ):
                options.append(
                    member_through_option(
                        continuous_member
                    )
                )

            return tuple(
                options
            )

        if is_right_angle_corner(
            first_member,
            second_member,
            tolerance_degrees=(
                right_angle_tolerance_degrees
            ),
        ):
            for member in persistent_members:
                options.append(
                    member_through_option(
                        member
                    )
                )

        options.append(
            both_mitered_option()
        )

        return tuple(
            options
        )

    # ---------------------------------------------------------
    # Three-or-more-member branch joint
    # ---------------------------------------------------------

    continuous_members = (
        continuous_members_for_multi_member_joint(
            members
        )
    )

    if len(
        continuous_members
    ) == 1:
        continuous_member = (
            continuous_members[
                0
            ]
        )

        if member_has_persistent_identity(
            continuous_member
        ):
            options.append(
                member_through_option(
                    continuous_member
                )
            )

            return tuple(
                options
            )

    # Ambiguous topology: preserve the complete option set rather
    # than hiding potentially valid fabrication choices.
    for member in persistent_members:
        options.append(
            member_through_option(
                member
            )
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
        str(
            layout_id
        ).strip()
        for layout_id
        in through_layout_ids
        if str(
            layout_id
        ).strip()
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
