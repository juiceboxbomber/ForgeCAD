"""Tests for generalized ForgeCAD cope specifications."""

import pytest

from forgecad.fabrication.joint import (
    Joint,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
)
from forgecad.fabrication.material import (
    Material,
)
from forgecad.fabrication.member import (
    Member,
)
from forgecad.fabrication.node import (
    Node,
)
from forgecad.fabrication.tube_profile import (
    TubeProfile,
)
from forgecad.services.joint_treatment_resolver import (
    CopeInstruction,
)
from forgecad.services.notch_analysis import (
    BRANCH_END_END,
    BRANCH_END_START,
    build_cope_specification,
    cope_specifications_for_treatment,
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


def test_builds_corner_cope_specification():
    joint, horizontal, vertical = (
        make_corner()
    )

    instruction = CopeInstruction(
        joint=joint,
        coped_member=vertical,
        target_member=horizontal,
    )

    specification = (
        build_cope_specification(
            instruction
        )
    )

    assert (
        specification.coped_member
        is vertical
    )

    assert (
        specification.target_member
        is horizontal
    )

    assert (
        specification.coped_end
        == BRANCH_END_START
    )

    assert (
        specification.angle_degrees
        == pytest.approx(
            90.0
        )
    )


def test_corner_target_diameter_comes_from_target_member():
    center = Node(
        0,
        0,
        0,
    )

    target = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
        profile(
            outside_diameter=50.8,
            wall_thickness=3.0,
        ),
    )

    coped = make_member(
        center,
        Node(
            0,
            500,
            0,
        ),
        profile(
            outside_diameter=31.75,
            wall_thickness=2.0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            target,
            coped,
        ],
    )

    specification = (
        build_cope_specification(
            CopeInstruction(
                joint=joint,
                coped_member=coped,
                target_member=target,
            )
        )
    )

    assert (
        specification.coped_outside_diameter
        == pytest.approx(
            31.75
        )
    )

    assert (
        specification.target_outside_diameter
        == pytest.approx(
            50.8
        )
    )


def test_reversed_coped_member_records_end():
    center = Node(
        0,
        0,
        0,
    )

    target = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    coped = make_member(
        Node(
            0,
            500,
            0,
        ),
        center,
    )

    joint = Joint(
        node=center,
        members=[
            target,
            coped,
        ],
    )

    specification = (
        build_cope_specification(
            CopeInstruction(
                joint=joint,
                coped_member=coped,
                target_member=target,
            )
        )
    )

    assert (
        specification.coped_end
        == BRANCH_END_END
    )


def test_member_through_corner_produces_one_cope():
    joint, horizontal, vertical = (
        make_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            horizontal,
        )
    )

    specifications = (
        cope_specifications_for_treatment(
            treatment
        )
    )

    assert len(
        specifications
    ) == 1

    assert (
        specifications[0].coped_member
        is vertical
    )

    assert (
        specifications[0].target_member
        is horizontal
    )


def test_opposite_corner_priority_reverses_cope():
    joint, horizontal, vertical = (
        make_corner()
    )

    treatment = (
        JointTreatment.member_through(
            joint,
            vertical,
        )
    )

    specifications = (
        cope_specifications_for_treatment(
            treatment
        )
    )

    assert len(
        specifications
    ) == 1

    assert (
        specifications[0].coped_member
        is horizontal
    )

    assert (
        specifications[0].target_member
        is vertical
    )


def test_both_coped_corner_produces_two_specs():
    joint, horizontal, vertical = (
        make_corner()
    )

    treatment = (
        JointTreatment.both_coped(
            joint
        )
    )

    specifications = (
        cope_specifications_for_treatment(
            treatment
        )
    )

    assert len(
        specifications
    ) == 2

    assert (
        specifications[0].coped_member
        is horizontal
    )

    assert (
        specifications[0].target_member
        is vertical
    )

    assert (
        specifications[1].coped_member
        is vertical
    )

    assert (
        specifications[1].target_member
        is horizontal
    )


def test_auto_corner_still_produces_no_specs():
    joint, horizontal, vertical = (
        make_corner()
    )

    treatment = (
        JointTreatment.automatic(
            joint
        )
    )

    assert (
        cope_specifications_for_treatment(
            treatment
        )
        == ()
    )


def test_collinear_cope_is_rejected():
    center = Node(
        0,
        0,
        0,
    )

    target = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    coped = make_member(
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
            target,
            coped,
        ],
    )

    with pytest.raises(
        ValueError
    ):
        build_cope_specification(
            CopeInstruction(
                joint=joint,
                coped_member=coped,
                target_member=target,
            )
        )


def test_member_cannot_cope_against_itself():
    center = Node(
        0,
        0,
        0,
    )

    member = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            member,
        ],
    )

    with pytest.raises(
        ValueError
    ):
        build_cope_specification(
            CopeInstruction(
                joint=joint,
                coped_member=member,
                target_member=member,
            )
        )
        