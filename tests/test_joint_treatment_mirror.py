"""Tests for mirroring ForgeCAD joint-treatment persistence data."""

import pytest

from forgecad.fabrication import (
    Node,
)
from forgecad.services.joint_treatment_mirror import (
    mirrored_treatment_data,
    mirror_node_key_across_centerline,
    mirror_node_key_across_plane,
    node_from_key,
    node_key_from_node,
    remap_through_layout_ids,
)


def test_node_key_round_trip():
    node = node_from_key(
        "100.000000,200.000000,300.000000"
    )

    assert node == Node(
        100.0,
        200.0,
        300.0,
    )

    assert (
        node_key_from_node(
            node
        )
        == "100.000000,200.000000,300.000000"
    )


def test_invalid_node_key_is_rejected():
    with pytest.raises(
        ValueError,
        match="node key",
    ):
        node_from_key(
            "100,200"
        )


def test_centerline_mirror_changes_joint_key():
    mirrored_key = (
        mirror_node_key_across_centerline(
            "300.000000,200.000000,50.000000",
            Node(
                100.0,
                -1000.0,
                0.0,
            ),
            Node(
                100.0,
                1000.0,
                0.0,
            ),
        )
    )

    assert mirrored_key == (
        "-100.000000,200.000000,50.000000"
    )


def test_plane_mirror_changes_joint_key():
    mirrored_key = (
        mirror_node_key_across_plane(
            "100.000000,250.000000,50.000000",
            "XZ",
        )
    )

    assert mirrored_key == (
        "100.000000,-250.000000,50.000000"
    )


def test_miter_treatment_copies_without_layout_ids():
    result = mirrored_treatment_data(
        "both_mitered",
        (),
        {},
    )

    assert result == (
        "both_mitered",
        (),
    )


def test_legacy_both_coped_treatment_copies():
    result = mirrored_treatment_data(
        "both_coped",
        (),
        {},
    )

    assert result == (
        "both_coped",
        (),
    )


def test_member_through_layout_id_is_remapped():
    result = mirrored_treatment_data(
        "member_through",
        (
            "L003",
        ),
        {
            "L003": "L014",
        },
    )

    assert result == (
        "member_through",
        (
            "L014",
        ),
    )


def test_through_pair_layout_ids_are_both_remapped():
    result = mirrored_treatment_data(
        "through_pair",
        (
            "L003",
            "L004",
        ),
        {
            "L003": "L014",
            "L004": "L015",
        },
    )

    assert result == (
        "through_pair",
        (
            "L014",
            "L015",
        ),
    )


def test_missing_mirrored_through_member_rejects_treatment():
    result = mirrored_treatment_data(
        "through_pair",
        (
            "L003",
            "L004",
        ),
        {
            "L003": "L014",
        },
    )

    assert result is None


def test_remap_never_leaves_original_layout_id():
    result = remap_through_layout_ids(
        (
            "L001",
        ),
        {
            "L001": "L009",
        },
    )

    assert result == (
        "L009",
    )

    assert "L001" not in result
    