"""Physical target extension when the coped/source member is bent."""

import ast
from math import (
    cos,
    radians,
    sin,
)
from pathlib import Path
from types import SimpleNamespace

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


ROOT = Path(__file__).resolve().parents[1]

RENDERER = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "renderer.py"
)


SOURCE_PROFILE = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)

TARGET_PROFILE = TubeProfile(
    outside_diameter=50.8,
    wall_thickness=3.048,
)

MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


def function_source(name):
    text = RENDERER.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        text
    )

    node = next(
        item
        for item in tree.body
        if isinstance(
            item,
            ast.FunctionDef,
        )
        and item.name == name
    )

    return ast.get_source_segment(
        text,
        node,
    )


def helper_for(specifications):
    namespace = {
        "explicit_cope_specifications_for_joint": (
            lambda document, joint, layout_ids: tuple(
                specifications
            )
        ),
    }

    exec(
        compile(
            function_source(
                "explicit_bent_target_extension_specifications_for_joint"
            ),
            str(RENDERER),
            "exec",
        ),
        namespace,
    )

    return namespace[
        "explicit_bent_target_extension_specifications_for_joint"
    ]


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
                StraightRun(
                    500.0
                ),
                StraightRun(
                    500.0
                ),
            ),
            bends=(
                Bend(
                    angle_degrees=90.0,
                    centerline_radius=100.0,
                ),
            ),
            profile=SOURCE_PROFILE,
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


def straight_target(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=TARGET_PROFILE,
        material=MATERIAL,
    )


def expected_extension(
    angle_degrees,
):
    source_radius = (
        SOURCE_PROFILE.outside_diameter
        / 2.0
    )

    target_radius = (
        TARGET_PROFILE.outside_diameter
        / 2.0
    )

    angle = radians(
        angle_degrees
    )

    return (
        source_radius
        + target_radius
        * abs(
            cos(
                angle
            )
        )
    ) / abs(
        sin(
            angle
        )
    )


def test_90_degree_straight_target_extends_for_bent_source():
    source = bent_member()

    target = straight_target(
        source.start,
        Node(
            0.0,
            500.0,
            0.0,
        ),
    )

    joint = Joint(
        node=source.start,
        members=[
            source,
            target,
        ],
    )

    result = helper_for(
        [
            SimpleNamespace(
                coped_member=source,
                target_member=target,
                target_outside_diameter=(
                    TARGET_PROFILE.outside_diameter
                ),
                angle_degrees=90.0,
            )
        ]
    )(
        object(),
        joint,
        {},
    )

    assert len(
        result
    ) == 1

    assert (
        result[0].member
        is target
    )

    assert (
        result[0].member_end
        == "start"
    )

    assert (
        result[0].extension_mm
        == pytest.approx(
            SOURCE_PROFILE.outside_diameter
            / 2.0
        )
    )


def test_45_degree_straight_target_gets_angle_aware_extension_for_bent_source():
    source = bent_member()

    target = straight_target(
        source.start,
        Node(
            500.0,
            500.0,
            0.0,
        ),
    )

    joint = Joint(
        node=source.start,
        members=[
            source,
            target,
        ],
    )

    result = helper_for(
        [
            SimpleNamespace(
                coped_member=source,
                target_member=target,
                target_outside_diameter=(
                    TARGET_PROFILE.outside_diameter
                ),
                angle_degrees=45.0,
            )
        ]
    )(
        object(),
        joint,
        {},
    )

    assert len(
        result
    ) == 1

    assert (
        result[0].extension_mm
        == pytest.approx(
            expected_extension(
                45.0
            )
        )
    )

    assert (
        result[0].extension_mm
        > SOURCE_PROFILE.outside_diameter
        / 2.0
    )


def test_straight_source_to_straight_target_remains_outside_this_rule():
    source = Member(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            -500.0,
            0.0,
            0.0,
        ),
        profile=SOURCE_PROFILE,
        material=MATERIAL,
    )

    target = straight_target(
        source.start,
        Node(
            0.0,
            500.0,
            0.0,
        ),
    )

    joint = Joint(
        node=source.start,
        members=[
            source,
            target,
        ],
    )

    result = helper_for(
        [
            SimpleNamespace(
                coped_member=source,
                target_member=target,
                target_outside_diameter=(
                    TARGET_PROFILE.outside_diameter
                ),
                angle_degrees=90.0,
            )
        ]
    )(
        object(),
        joint,
        {},
    )

    assert result == ()
