"""Regression tests for joints on continuous members."""

from forgecad.fabrication import (
    Frame,
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
    JointTreatmentMode,
)
from forgecad.services.joint_extension import (
    member_through_extensions,
)
from forgecad.services.joint_geometry import (
    JOINT_T,
    classify_joint,
)
from forgecad.services.joint_member_roles import (
    identify_member_roles,
)
from forgecad.services.joint_service import (
    connected_members,
    detect_joints,
    member_touches_node,
)


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def make_material():
    return Material(
        name="DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def make_member(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=make_profile(),
        material=make_material(),
    )


def test_continuous_member_touches_interior_node():
    center = Node(
        500,
        0,
        0,
    )

    continuous = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            1000,
            0,
            0,
        ),
    )

    assert member_touches_node(
        continuous,
        center,
    )


def test_connected_members_include_continuous_member_and_branch():
    center = Node(
        500,
        0,
        0,
    )

    continuous = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            1000,
            0,
            0,
        ),
    )

    branch = make_member(
        center,
        Node(
            500,
            500,
            0,
        ),
    )

    frame = Frame(
        members=[
            continuous,
            branch,
        ]
    )

    connected = connected_members(
        frame,
        center,
    )

    assert len(
        connected
    ) == 2

    assert continuous in connected
    assert branch in connected


def test_detects_t_joint_on_continuous_member():
    center = Node(
        500,
        0,
        0,
    )

    continuous = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            1000,
            0,
            0,
        ),
    )

    branch = make_member(
        center,
        Node(
            500,
            500,
            0,
        ),
    )

    frame = Frame(
        members=[
            continuous,
            branch,
        ]
    )

    joints = detect_joints(
        frame
    )

    matching = [
        joint
        for joint in joints
        if joint.node == center
    ]

    assert len(
        matching
    ) == 1

    joint = matching[
        0
    ]

    assert joint.member_count == 2

    assert classify_joint(
        joint
    ) == JOINT_T


def test_continuous_member_is_through_and_branch_is_branch():
    center = Node(
        500,
        0,
        0,
    )

    continuous = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            1000,
            0,
            0,
        ),
    )

    branch = make_member(
        center,
        Node(
            500,
            500,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            continuous,
            branch,
        ],
    )

    roles = identify_member_roles(
        joint
    )

    assert roles.through_members == (
        continuous,
    )

    assert roles.branch_members == (
        branch,
    )


def test_continuous_through_member_requires_no_extension():
    center = Node(
        500,
        0,
        0,
    )

    continuous = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            1000,
            0,
            0,
        ),
    )

    branch = make_member(
        center,
        Node(
            500,
            500,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            continuous,
            branch,
        ],
    )

    treatment = JointTreatment(
        joint=joint,
        mode=(
            JointTreatmentMode.MEMBER_THROUGH
        ),
        through_members=(
            continuous,
        ),
    )

    assert member_through_extensions(
        treatment
    ) == ()
    