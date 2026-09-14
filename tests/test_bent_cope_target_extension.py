"""Regression tests for physical extension of bent cope targets."""

import ast
from math import cos, radians, sin
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
from forgecad.geometry import Vector3D


ROOT = Path(__file__).resolve().parents[1]
RENDERER = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "renderer.py"
)


def function_source(name):
    text = RENDERER.read_text(encoding="utf-8")
    tree = ast.parse(text)
    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef)
        and item.name == name
    )
    return ast.get_source_segment(text, node)


TARGET_PROFILE = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)

SOURCE_PROFILE = TubeProfile(
    outside_diameter=50.8,
    wall_thickness=3.048,
)

MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


def bent_member():
    return BentMember(
        start=Node(0.0, 0.0, 0.0),
        end=Node(600.0, 600.0, 0.0),
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
            profile=TARGET_PROFILE,
            material=MATERIAL,
        ),
        initial_direction=Vector3D(1.0, 0.0, 0.0),
        initial_bend_normal=Vector3D(0.0, 0.0, 1.0),
    )


def straight(start, end):
    return Member(
        start=start,
        end=end,
        profile=SOURCE_PROFILE,
        material=MATERIAL,
    )


def helper_for(specifications):
    namespace = {
        "explicit_cope_specifications_for_joint": (
            lambda document, joint, layout_ids: tuple(specifications)
        ),
    }

    exec(
        function_source(
            "explicit_bent_target_extension_specifications_for_joint"
        ),
        namespace,
    )

    return namespace[
        "explicit_bent_target_extension_specifications_for_joint"
    ]


def expected_extension(angle_degrees):
    source_radius = SOURCE_PROFILE.outside_diameter / 2.0
    target_radius = TARGET_PROFILE.outside_diameter / 2.0
    angle = radians(angle_degrees)

    return (
        source_radius
        + target_radius * abs(cos(angle))
    ) / abs(sin(angle))


def test_90_degree_bent_target_extension_equals_source_radius():
    bent = bent_member()
    source = straight(
        bent.start,
        Node(0.0, -500.0, 0.0),
    )
    joint = Joint(
        node=bent.start,
        members=[source, bent],
    )

    result = helper_for([
        SimpleNamespace(
            coped_member=source,
            target_member=bent,
            target_outside_diameter=TARGET_PROFILE.outside_diameter,
            angle_degrees=90.0,
        )
    ])(
        object(),
        joint,
        {},
    )

    assert len(result) == 1
    assert result[0].member is bent
    assert result[0].member_end == "start"
    assert result[0].extension_mm == pytest.approx(
        SOURCE_PROFILE.outside_diameter / 2.0
    )


def test_45_degree_bent_target_extension_covers_full_intersection():
    bent = bent_member()
    source = straight(
        bent.end,
        Node(950.0, 950.0, 0.0),
    )
    joint = Joint(
        node=bent.end,
        members=[source, bent],
    )

    result = helper_for([
        SimpleNamespace(
            coped_member=source,
            target_member=bent,
            target_outside_diameter=TARGET_PROFILE.outside_diameter,
            angle_degrees=45.0,
        )
    ])(
        object(),
        joint,
        {},
    )

    assert len(result) == 1
    assert result[0].member_end == "end"
    assert result[0].extension_mm == pytest.approx(
        expected_extension(45.0)
    )
    assert result[0].extension_mm > (
        SOURCE_PROFILE.outside_diameter / 2.0
    )


def test_30_degree_extension_is_longer_than_45_degree_extension():
    assert expected_extension(30.0) > expected_extension(45.0)


def test_straight_target_is_unchanged_by_bent_target_extension_rule():
    source = straight(
        Node(0.0, 0.0, 0.0),
        Node(-500.0, 0.0, 0.0),
    )
    target = straight(
        Node(0.0, 0.0, 0.0),
        Node(500.0, 0.0, 0.0),
    )
    joint = Joint(
        node=source.start,
        members=[source, target],
    )

    result = helper_for([
        SimpleNamespace(
            coped_member=source,
            target_member=target,
            target_outside_diameter=TARGET_PROFILE.outside_diameter,
            angle_degrees=45.0,
        )
    ])(
        object(),
        joint,
        {},
    )

    assert result == ()


def test_frame_extension_collection_still_includes_bent_target_rule():
    source = function_source(
        "extension_specifications_for_frame"
    )

    assert (
        "explicit_bent_target_extension_specifications_for_joint"
        in source
    )
