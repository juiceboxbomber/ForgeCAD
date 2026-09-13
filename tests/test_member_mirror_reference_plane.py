"""Tests for offset-plane member mirroring."""

from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services.member_mirror import (
    mirror_member_across_plane,
    mirror_node_across_plane,
)


def profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def material():
    return Material(
        name="DOM Steel",
        density=7850.0,
        yield_strength=350.0,
    )


def test_xy_offset_plane_mirrors_z_about_offset():
    result = mirror_node_across_plane(
        Node(
            10.0,
            20.0,
            1000.0,
        ),
        "XY",
        offset=1200.0,
    )

    assert result == Node(
        10.0,
        20.0,
        1400.0,
    )


def test_xz_offset_plane_mirrors_y_about_offset():
    result = mirror_node_across_plane(
        Node(
            10.0,
            100.0,
            20.0,
        ),
        "XZ",
        offset=250.0,
    )

    assert result == Node(
        10.0,
        400.0,
        20.0,
    )


def test_yz_offset_plane_mirrors_x_about_negative_offset():
    result = mirror_node_across_plane(
        Node(
            100.0,
            20.0,
            30.0,
        ),
        "YZ",
        offset=-200.0,
    )

    assert result == Node(
        -500.0,
        20.0,
        30.0,
    )


def test_zero_offset_preserves_original_global_plane_behavior():
    result = mirror_node_across_plane(
        Node(
            10.0,
            20.0,
            30.0,
        ),
        "XZ",
    )

    assert result == Node(
        10.0,
        -20.0,
        30.0,
    )


def test_member_offset_plane_preserves_profile_and_material():
    source = Member(
        start=Node(
            0.0,
            100.0,
            0.0,
        ),
        end=Node(
            500.0,
            100.0,
            250.0,
        ),
        profile=profile(),
        material=material(),
    )

    result = mirror_member_across_plane(
        source,
        "XZ",
        offset=250.0,
    )

    assert result.start == Node(
        0.0,
        400.0,
        0.0,
    )

    assert result.end == Node(
        500.0,
        400.0,
        250.0,
    )

    assert result.profile is source.profile
    assert result.material is source.material
