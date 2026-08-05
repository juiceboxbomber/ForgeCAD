import pytest

from forgecad import FrameLayout, LayoutLine
from forgecad.geometry import Point3D
from forgecad.services import (
    build_frame_from_layout,
    create_project,
)


def test_build_frame_from_layout():
    project = create_project("Layout Test")

    a = Point3D(0, 0, 0)
    b = Point3D(1000, 0, 0)
    c = Point3D(1000, 600, 0)

    layout = FrameLayout(
        lines=[
            LayoutLine(a, b),
            LayoutLine(b, c),
        ]
    )

    frame = build_frame_from_layout(project, layout)

    assert frame.node_count == 3
    assert frame.member_count == 2
    assert frame.members[0].length == pytest.approx(1000)
    assert frame.members[1].length == pytest.approx(600)


def test_members_use_active_profile():
    project = create_project(
        name="Profile Test",
        active_profile_name="1.250 x .095 DOM",
    )

    layout = FrameLayout(
        lines=[
            LayoutLine(
                Point3D(0, 0, 0),
                Point3D(500, 0, 0),
            )
        ]
    )

    frame = build_frame_from_layout(project, layout)

    assert (
        frame.members[0].profile
        is project.tube_library.active_profile
    )


def test_members_use_default_material():
    project = create_project("Material Test")

    layout = FrameLayout(
        lines=[
            LayoutLine(
                Point3D(0, 0, 0),
                Point3D(500, 0, 0),
            )
        ]
    )

    frame = build_frame_from_layout(project, layout)

    assert frame.members[0].material is project.default_material


def test_missing_default_material_is_rejected():
    project = create_project("Missing Material")
    project.default_material = None

    layout = FrameLayout(
        lines=[
            LayoutLine(
                Point3D(0, 0, 0),
                Point3D(500, 0, 0),
            )
        ]
    )

    with pytest.raises(ValueError):
        build_frame_from_layout(project, layout)


def test_empty_layout_creates_empty_frame():
    project = create_project("Empty Layout")

    frame = build_frame_from_layout(
        project,
        FrameLayout(),
    )

    assert frame.node_count == 0
    assert frame.member_count == 0
    