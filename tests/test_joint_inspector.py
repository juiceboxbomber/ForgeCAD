"""Tests for ForgeCAD joint inspection services."""

from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services.joint_inspector import (
    inspect_joint,
)


PROFILE = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)

MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
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


def test_inspects_t_joint():
    joint_node = Node(
        0,
        0,
        0,
    )

    left = make_member(
        joint_node,
        Node(
            -500,
            0,
            0,
        ),
    )

    right = make_member(
        joint_node,
        Node(
            500,
            0,
            0,
        ),
    )

    branch = make_member(
        joint_node,
        Node(
            0,
            500,
            0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            left,
            right,
            branch,
        ],
    )

    inspection = inspect_joint(
        joint
    )

    assert (
        inspection.classification
        == "t_joint"
    )

    assert (
        inspection.member_count
        == 3
    )

    assert (
        inspection.through_member_count
        == 2
    )

    assert (
        inspection.branch_member_count
        == 1
    )

    assert (
        inspection.notch_count
        == 1
    )


def test_t_joint_member_roles():
    joint_node = Node(
        0,
        0,
        0,
    )

    left = make_member(
        joint_node,
        Node(
            -500,
            0,
            0,
        ),
    )

    right = make_member(
        joint_node,
        Node(
            500,
            0,
            0,
        ),
    )

    branch = make_member(
        joint_node,
        Node(
            0,
            500,
            0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            left,
            right,
            branch,
        ],
    )

    inspection = inspect_joint(
        joint
    )

    roles = {
        id(item.member): item.role
        for item in inspection.members
    }

    assert roles[
        id(left)
    ] == "through"

    assert roles[
        id(right)
    ] == "through"

    assert roles[
        id(branch)
    ] == "branch"


def test_t_joint_angles_are_reported():
    joint_node = Node(
        0,
        0,
        0,
    )

    left = make_member(
        joint_node,
        Node(
            -500,
            0,
            0,
        ),
    )

    right = make_member(
        joint_node,
        Node(
            500,
            0,
            0,
        ),
    )

    branch = make_member(
        joint_node,
        Node(
            0,
            500,
            0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            left,
            right,
            branch,
        ],
    )

    inspection = inspect_joint(
        joint
    )

    angles = sorted(
        round(
            item.angle_degrees,
            6,
        )
        for item in inspection.angles
    )

    assert angles == [
        90.0,
        90.0,
        180.0,
    ]


def test_t_joint_notch_information():
    joint_node = Node(
        0,
        0,
        0,
    )

    left = make_member(
        joint_node,
        Node(
            -500,
            0,
            0,
        ),
    )

    right = make_member(
        joint_node,
        Node(
            500,
            0,
            0,
        ),
    )

    branch = make_member(
        joint_node,
        Node(
            0,
            500,
            0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            left,
            right,
            branch,
        ],
    )

    inspection = inspect_joint(
        joint
    )

    notch = inspection.notches[
        0
    ]

    assert (
        notch.branch_member
        is branch
    )

    assert (
        notch.branch_end
        == "start"
    )

    assert round(
        notch.angle_degrees,
        6,
    ) == 90.0

    assert (
        notch.branch_outside_diameter_mm
        == PROFILE.outside_diameter
    )

    assert (
        notch.through_outside_diameter_mm
        == PROFILE.outside_diameter
    )


def test_corner_has_no_notch():
    joint_node = Node(
        0,
        0,
        0,
    )

    first = make_member(
        joint_node,
        Node(
            500,
            0,
            0,
        ),
    )

    second = make_member(
        joint_node,
        Node(
            0,
            500,
            0,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            first,
            second,
        ],
    )

    inspection = inspect_joint(
        joint
    )

    assert (
        inspection.classification
        == "corner"
    )

    assert (
        inspection.notch_count
        == 0
    )

    assert (
        inspection.through_member_count
        == 0
    )

    assert (
        inspection.branch_member_count
        == 2
    )
    