"""Tests for ForgeCAD joint fabrication extensions."""

import math

import pytest

from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
)
from forgecad.services.joint_extension import (
    MEMBER_END_END,
    MEMBER_END_START,
    extension_specifications_for_treatment,
    extension_to_outer_surface,
    fabrication_angle,
    member_end_at_joint,
    member_through_extension,
)


MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


def profile(
    outside_diameter=44.45,
    wall_thickness=3.048,
):
    return TubeProfile(
        outside_diameter=outside_diameter,
        wall_thickness=wall_thickness,
    )


def make_member(
    start,
    end,
    tube_profile=None,
):
    return Member(
        start=start,
        end=end,
        profile=(
            tube_profile
            or profile()
        ),
        material=MATERIAL,
    )


def make_corner():
    center = Node(
        0,
        0,
        0,
    )

    horizontal = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    vertical = make_member(
        center,
        Node(
            0,
            500,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            horizontal,
            vertical,
        ],
    )

    return (
        joint,
        horizontal,
        vertical,
    )


def make_60_degree_corner():
    """Return a two-member 60-degree corner."""

    center = Node(
        0,
        0,
        0,
    )

    first = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    angle = math.radians(
        60.0
    )

    second = make_member(
        center,
        Node(
            500.0
            * math.cos(
                angle
            ),
            500.0
            * math.sin(
                angle
            ),
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            first,
            second,
        ],
    )

    return (
        joint,
        first,
        second,
    )


def test_member_end_at_joint_detects_start():
    joint, first, second = (
        make_corner()
    )

    assert (
        member_end_at_joint(
            first,
            joint,
        )
        == MEMBER_END_START
    )


def test_member_end_at_joint_detects_end():
    center = Node(
        0,
        0,
        0,
    )

    member = make_member(
        Node(
            500,
            0,
            0,
        ),
        center,
    )

    joint = Joint(
        node=center,
        members=[
            member,
        ],
    )

    assert (
        member_end_at_joint(
            member,
            joint,
        )
        == MEMBER_END_END
    )


def test_corner_fabrication_angle_is_90_degrees():
    joint, first, second = (
        make_corner()
    )

    assert fabrication_angle(
        first,
        second,
        joint,
    ) == pytest.approx(
        90.0
    )


def test_90_degree_miter_extension_equals_other_tube_radius():
    joint, first, second = (
        make_corner()
    )

    extension = (
        extension_to_outer_surface(
            first,
            second,
            joint,
        )
    )

    assert extension == pytest.approx(
        44.45 / 2.0
    )


def test_miter_extension_uses_intersecting_tube_radius():
    center = Node(
        0,
        0,
        0,
    )

    first = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
        profile(
            outside_diameter=31.75,
        ),
    )

    second = make_member(
        center,
        Node(
            0,
            500,
            0,
        ),
        profile(
            outside_diameter=50.8,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            first,
            second,
        ],
    )

    extension = (
        extension_to_outer_surface(
            first,
            second,
            joint,
        )
    )

    assert extension == pytest.approx(
        25.4
    )


def test_60_degree_miter_extension_is_angle_corrected():
    joint, first, second = (
        make_60_degree_corner()
    )

    extension = (
        extension_to_outer_surface(
            first,
            second,
            joint,
        )
    )

    expected = (
        (44.45 / 2.0)
        / math.sin(
            math.radians(
                60.0
            )
        )
    )

    assert extension == pytest.approx(
        expected
    )

    assert extension > (
        44.45 / 2.0
    )


def test_member_through_extension_equals_intersecting_radius():
    joint, first, second = (
        make_corner()
    )

    extension = (
        member_through_extension(
            second
        )
    )

    assert extension == pytest.approx(
        44.45 / 2.0
    )


def test_member_through_extension_uses_intersecting_profile():
    joint, first, second = (
        make_corner()
    )

    larger_profile = profile(
        outside_diameter=50.8,
    )

    larger_member = make_member(
        second.start,
        second.end,
        larger_profile,
    )

    extension = (
        member_through_extension(
            larger_member
        )
    )

    assert extension == pytest.approx(
        25.4
    )


def test_member_through_extends_selected_member_only():
    """
    Member Through extends only the selected through member.

    The coped member retains its design endpoint and is shaped
    by the cope operation.
    """

    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            first,
        )
    )

    specifications = (
        extension_specifications_for_treatment(
            treatment
        )
    )

    assert len(
        specifications
    ) == 1

    specification = (
        specifications[
            0
        ]
    )

    assert (
        specification.member
        is first
    )

    assert (
        specification.member_end
        == MEMBER_END_START
    )

    assert (
        specification.extension_mm
        == pytest.approx(
            44.45 / 2.0
        )
    )


def test_reversing_member_through_extends_other_selected_member():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            second,
        )
    )

    specifications = (
        extension_specifications_for_treatment(
            treatment
        )
    )

    assert len(
        specifications
    ) == 1

    assert (
        specifications[
            0
        ].member
        is second
    )

    assert (
        specifications[
            0
        ].member_end
        == MEMBER_END_START
    )


def test_angled_member_through_extends_selected_member_only():
    """
    An angled Member Through still extends only the selected
    through tube.
    """

    joint, first, second = (
        make_60_degree_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            first,
        )
    )

    specifications = (
        extension_specifications_for_treatment(
            treatment
        )
    )

    assert len(
        specifications
    ) == 1

    assert (
        specifications[
            0
        ].member
        is first
    )


def test_angled_member_through_uses_radius_not_projected_distance():
    """
    Member Through is a physical continuation to the outside
    surface of the other tube.

    Its extension therefore remains one intersecting-tube
    radius even when the joint is angled.
    """

    joint, first, second = (
        make_60_degree_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            first,
        )
    )

    specifications = (
        extension_specifications_for_treatment(
            treatment
        )
    )

    radius = (
        44.45 / 2.0
    )

    projected_distance = (
        radius
        / math.sin(
            math.radians(
                60.0
            )
        )
    )

    assert (
        specifications[
            0
        ].extension_mm
        == pytest.approx(
            radius
        )
    )

    assert (
        specifications[
            0
        ].extension_mm
        < projected_distance
    )


def test_both_coped_extends_both_members():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.both_coped(
            joint
        )
    )

    specifications = (
        extension_specifications_for_treatment(
            treatment
        )
    )

    assert len(
        specifications
    ) == 2

    assert {
        specification.member
        for specification
        in specifications
    } == {
        first,
        second,
    }

    assert (
        specifications[
            0
        ].extension_mm
        == pytest.approx(
            44.45 / 2.0
        )
    )

    assert (
        specifications[
            1
        ].extension_mm
        == pytest.approx(
            44.45 / 2.0
        )
    )


def test_angled_both_coped_keeps_angle_corrected_extension():
    """
    Unlike Member Through, miter stock is angle corrected.
    """

    joint, first, second = (
        make_60_degree_corner()
    )

    treatment = (
        JointTreatment.both_coped(
            joint
        )
    )

    specifications = (
        extension_specifications_for_treatment(
            treatment
        )
    )

    expected = (
        (44.45 / 2.0)
        / math.sin(
            math.radians(
                60.0
            )
        )
    )

    assert len(
        specifications
    ) == 2

    assert (
        specifications[
            0
        ].extension_mm
        == pytest.approx(
            expected
        )
    )

    assert (
        specifications[
            1
        ].extension_mm
        == pytest.approx(
            expected
        )
    )


def test_auto_corner_has_no_explicit_extension():
    joint, first, second = (
        make_corner()
    )

    treatment = (
        JointTreatment.automatic(
            joint
        )
    )

    assert (
        extension_specifications_for_treatment(
            treatment
        )
        == ()
    )


def test_through_pair_has_no_extension():
    center = Node(
        0,
        0,
        0,
    )

    left = make_member(
        center,
        Node(
            -500,
            0,
            0,
        ),
    )

    right = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    branch = make_member(
        center,
        Node(
            0,
            500,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            left,
            right,
            branch,
        ],
    )

    treatment = (
        JointTreatment.through_pair(
            joint,
            left,
            right,
        )
    )

    assert (
        extension_specifications_for_treatment(
            treatment
        )
        == ()
    )


def test_collinear_miter_extension_is_rejected():
    center = Node(
        0,
        0,
        0,
    )

    first = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    second = make_member(
        center,
        Node(
            250,
            0,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            first,
            second,
        ],
    )

    with pytest.raises(
        ValueError
    ):
        extension_to_outer_surface(
            first,
            second,
            joint,
        )
        