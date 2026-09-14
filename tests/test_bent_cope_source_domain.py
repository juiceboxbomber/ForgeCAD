"""Domain regressions for a bent member used as the Cope Selected source."""

import pytest

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Joint,
    Material,
    Member,
    Node,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import (
    Vector3D,
)
from forgecad.services.joint_treatment_resolver import (
    CopeInstruction,
)
from forgecad.services.notch_analysis import (
    BRANCH_END_END,
    BRANCH_END_START,
    build_cope_specification,
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


def bent_member():
    return BentMember(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            600.0,
            600.0,
            0.0,
        ),
        tube=BentTube(
            straight_runs=(
                StraightRun(500.0),
                StraightRun(500.0),
            ),
            bends=(
                Bend(
                    angle_degrees=90.0,
                    centerline_radius=100.0,
                ),
            ),
            profile=PROFILE,
            material=MATERIAL,
        ),
        initial_direction=Vector3D(
            1.0,
            0.0,
            0.0,
        ),
        initial_bend_normal=Vector3D(
            0.0,
            0.0,
            1.0,
        ),
    )


def test_bent_source_start_builds_cope_from_local_tangent():
    bent = bent_member()

    target = Member(
        start=bent.start,
        end=Node(
            0.0,
            500.0,
            0.0,
        ),
        profile=PROFILE,
        material=MATERIAL,
    )

    joint = Joint(
        node=bent.start,
        members=[
            bent,
            target,
        ],
    )

    specification = build_cope_specification(
        CopeInstruction(
            joint=joint,
            coped_member=bent,
            target_member=target,
        )
    )

    assert specification.coped_member is bent
    assert specification.coped_end == BRANCH_END_START
    assert specification.angle_degrees == pytest.approx(
        90.0
    )


def test_bent_source_end_builds_cope_from_local_tangent():
    bent = bent_member()

    target = Member(
        start=bent.end,
        end=Node(
            1100.0,
            600.0,
            0.0,
        ),
        profile=PROFILE,
        material=MATERIAL,
    )

    joint = Joint(
        node=bent.end,
        members=[
            bent,
            target,
        ],
    )

    specification = build_cope_specification(
        CopeInstruction(
            joint=joint,
            coped_member=bent,
            target_member=target,
        )
    )

    assert specification.coped_member is bent
    assert specification.coped_end == BRANCH_END_END
    assert specification.angle_degrees == pytest.approx(
        90.0
    )


def test_bent_source_endpoint_resolution_tolerates_small_cad_roundoff():
    bent = bent_member()

    joint_node = Node(
        600.0000004,
        600.0,
        0.0,
    )

    target = Member(
        start=joint_node,
        end=Node(
            1100.0,
            600.0,
            0.0,
        ),
        profile=PROFILE,
        material=MATERIAL,
    )

    joint = Joint(
        node=joint_node,
        members=[
            bent,
            target,
        ],
    )

    specification = build_cope_specification(
        CopeInstruction(
            joint=joint,
            coped_member=bent,
            target_member=target,
        )
    )

    assert specification.coped_end == BRANCH_END_END
