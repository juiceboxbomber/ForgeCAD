"""Tests for ForgeCAD joint miter analysis."""

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
from forgecad.services.joint_miter import (
    equal_miter_plane_normal,
    member_direction_from_joint,
    member_keep_point,
    miter_specifications_for_treatment,
)


MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


PROFILE = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)


def make_member(
    start,
    end,
):
    """Create a test member."""

    return Member(
        start=start,
        end=end,
        profile=PROFILE,
        material=MATERIAL,
    )


def make_corner():
    """Create a 90-degree two-member corner."""

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


def test_member_direction_points_away_from_joint():
    joint, horizontal, vertical = (
        make_corner()
    )

    direction = (
        member_direction_from_joint(
            horizontal,
            joint,
        )
    )

    assert direction.x == pytest.approx(
        1.0
    )

    assert direction.y == pytest.approx(
        0.0
    )

    assert direction.z == pytest.approx(
        0.0
    )


def test_member_direction_handles_joint_at_end():
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

    direction = (
        member_direction_from_joint(
            member,
            joint,
        )
    )

    assert direction.x == pytest.approx(
        1.0
    )


def test_keep_point_is_endpoint_away_from_joint():
    joint, horizontal, vertical = (
        make_corner()
    )

    assert member_keep_point(
        horizontal,
        joint,
    ) == (
        500.0,
        0.0,
        0.0,
    )


def test_90_degree_miter_plane_normal_is_perpendicular_to_bisector():
    joint, horizontal, vertical = (
        make_corner()
    )

    normal = (
        equal_miter_plane_normal(
            horizontal,
            vertical,
            joint,
        )
    )

    expected = (
        1.0
        / math.sqrt(
            2.0
        )
    )

    assert normal[
        0
    ] == pytest.approx(
        expected
    )

    assert normal[
        1
    ] == pytest.approx(
        -expected
    )

    assert normal[
        2
    ] == pytest.approx(
        0.0
    )


def test_miter_normal_is_unit_length():
    joint, horizontal, vertical = (
        make_corner()
    )

    normal = (
        equal_miter_plane_normal(
            horizontal,
            vertical,
            joint,
        )
    )

    length = math.sqrt(
        normal[0] ** 2
        + normal[1] ** 2
        + normal[2] ** 2
    )

    assert length == pytest.approx(
        1.0
    )


def test_miter_normal_is_perpendicular_to_internal_bisector():
    joint, horizontal, vertical = (
        make_corner()
    )

    normal = (
        equal_miter_plane_normal(
            horizontal,
            vertical,
            joint,
        )
    )

    expected = (
        1.0
        / math.sqrt(
            2.0
        )
    )

    bisector = (
        expected,
        expected,
        0.0,
    )

    dot = (
        normal[0] * bisector[0]
        + normal[1] * bisector[1]
        + normal[2] * bisector[2]
    )

    assert dot == pytest.approx(
        0.0
    )


def test_non_90_degree_corner_plane_follows_angle_bisector():
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

    normal = (
        equal_miter_plane_normal(
            first,
            second,
            joint,
        )
    )

    # The miter plane itself follows the 30-degree
    # internal bisector. Its normal must therefore
    # be perpendicular to that direction.
    bisector = (
        math.cos(
            math.radians(
                30.0
            )
        ),
        math.sin(
            math.radians(
                30.0
            )
        ),
        0.0,
    )

    dot = (
        normal[0] * bisector[0]
        + normal[1] * bisector[1]
        + normal[2] * bisector[2]
    )

    assert dot == pytest.approx(
        0.0,
        abs=1e-9,
    )


def test_both_coped_treatment_creates_two_miter_specs():
    joint, horizontal, vertical = (
        make_corner()
    )

    treatment = (
        JointTreatment.both_coped(
            joint
        )
    )

    specifications = (
        miter_specifications_for_treatment(
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
        horizontal,
        vertical,
    }


def test_both_members_share_exact_miter_plane():
    joint, horizontal, vertical = (
        make_corner()
    )

    treatment = (
        JointTreatment.both_coped(
            joint
        )
    )

    specifications = (
        miter_specifications_for_treatment(
            treatment
        )
    )

    first = specifications[
        0
    ]

    second = specifications[
        1
    ]

    assert (
        first.plane_point
        == second.plane_point
    )

    assert (
        first.plane_normal
        == second.plane_normal
    )


def test_miter_plane_passes_through_joint():
    joint, horizontal, vertical = (
        make_corner()
    )

    treatment = (
        JointTreatment.both_coped(
            joint
        )
    )

    specifications = (
        miter_specifications_for_treatment(
            treatment
        )
    )

    assert (
        specifications[
            0
        ].plane_point
        == (
            0.0,
            0.0,
            0.0,
        )
    )


def test_each_member_keeps_its_outer_endpoint():
    joint, horizontal, vertical = (
        make_corner()
    )

    treatment = (
        JointTreatment.both_coped(
            joint
        )
    )

    specifications = (
        miter_specifications_for_treatment(
            treatment
        )
    )

    assert (
        specifications[
            0
        ].keep_point
        == (
            500.0,
            0.0,
            0.0,
        )
    )

    assert (
        specifications[
            1
        ].keep_point
        == (
            0.0,
            500.0,
            0.0,
        )
    )


def test_member_through_does_not_create_miter():
    joint, horizontal, vertical = (
        make_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            horizontal,
        )
    )

    assert (
        miter_specifications_for_treatment(
            treatment
        )
        == ()
    )


def test_automatic_does_not_create_miter():
    joint, horizontal, vertical = (
        make_corner()
    )

    treatment = (
        JointTreatment.automatic(
            joint
        )
    )

    assert (
        miter_specifications_for_treatment(
            treatment
        )
        == ()
    )


def test_same_direction_members_cannot_be_equal_mitered():
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

    treatment = (
        JointTreatment.both_coped(
            joint
        )
    )

    with pytest.raises(
        ValueError
    ):
        miter_specifications_for_treatment(
            treatment
        )
        