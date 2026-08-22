"""Tests for offset-plane joint-treatment mirroring."""

from forgecad.services.joint_treatment_mirror import (
    mirror_node_key_across_plane,
)


def test_joint_key_mirrors_across_offset_xz_plane():
    result = mirror_node_key_across_plane(
        "100.000000,50.000000,25.000000",
        "XZ",
        offset=200.0,
    )

    assert result == (
        "100.000000,350.000000,25.000000"
    )


def test_joint_key_global_plane_default_is_unchanged():
    result = mirror_node_key_across_plane(
        "100.000000,50.000000,25.000000",
        "YZ",
    )

    assert result == (
        "-100.000000,50.000000,25.000000"
    )
