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


def test_90_degree_extension_equals_other_tube_radius():
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


def test_extension_uses_intersecting_tube_radius():
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


def test_60_degree_corner_extends_farther_than_radius():
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
            500.0 * math.cos(angle),
            500.0 * math.sin(angle),
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


def test_member_through_extends_selected_member():
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

    assert specification.extension_mm == pytest.approx(
        44.45 / 2.0
    )


def test_reversing_corner_priority_extends_other_member():
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

    assert (
        specifications[
            0
        ].member
        is second
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


def test_collinear_extension_is_rejected():
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
        