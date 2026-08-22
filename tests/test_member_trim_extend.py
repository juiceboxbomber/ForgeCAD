"""Tests for ForgeCAD Trim/Extend member geometry."""

import pytest

from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services.member_trim_extend import (
    classify_parameter,
    line_intersection_3d,
    modification_kind,
    replace_member_endpoint,
)


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def make_material():
    return Material(
        name="DOM Steel",
        density=7850.0,
        yield_strength=350.0,
    )


def member(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=make_profile(),
        material=make_material(),
    )


def test_perpendicular_xy_lines_intersect():
    first = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        Node(
            500.0,
            -500.0,
            0.0,
        ),
        Node(
            500.0,
            500.0,
            0.0,
        ),
    )

    point, first_t, second_t = (
        line_intersection_3d(
            first,
            second,
        )
    )

    assert point == Node(
        500.0,
        0.0,
        0.0,
    )

    assert first_t == pytest.approx(
        0.5
    )

    assert second_t == pytest.approx(
        0.5
    )


def test_true_3d_lines_intersect():
    first = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            1000.0,
        ),
    )

    second = member(
        Node(
            500.0,
            -500.0,
            500.0,
        ),
        Node(
            500.0,
            500.0,
            500.0,
        ),
    )

    point, first_t, second_t = (
        line_intersection_3d(
            first,
            second,
        )
    )

    assert point == Node(
        500.0,
        0.0,
        500.0,
    )

    assert first_t == pytest.approx(
        0.5
    )

    assert second_t == pytest.approx(
        0.5
    )


def test_lines_that_only_cross_in_projection_are_rejected():
    first = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        Node(
            500.0,
            -500.0,
            100.0,
        ),
        Node(
            500.0,
            500.0,
            100.0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="3D",
    ):
        line_intersection_3d(
            first,
            second,
        )


def test_parallel_lines_are_rejected():
    first = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        Node(
            0.0,
            100.0,
            0.0,
        ),
        Node(
            1000.0,
            100.0,
            0.0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Parallel",
    ):
        line_intersection_3d(
            first,
            second,
        )


def test_collinear_lines_are_rejected():
    first = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        Node(
            500.0,
            0.0,
            0.0,
        ),
        Node(
            1500.0,
            0.0,
            0.0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Collinear",
    ):
        line_intersection_3d(
            first,
            second,
        )


def test_intersection_beyond_end_is_reported():
    first = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        Node(
            1000.0,
            -500.0,
            0.0,
        ),
        Node(
            1000.0,
            500.0,
            0.0,
        ),
    )

    point, first_t, second_t = (
        line_intersection_3d(
            first,
            second,
        )
    )

    assert point == Node(
        1000.0,
        0.0,
        0.0,
    )

    assert first_t == pytest.approx(
        2.0
    )

    assert second_t == pytest.approx(
        0.5
    )

    assert (
        modification_kind(
            first_t
        )
        == "extend"
    )


def test_intersection_before_start_is_reported():
    first = member(
        Node(
            500.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    second = member(
        Node(
            0.0,
            -500.0,
            0.0,
        ),
        Node(
            0.0,
            500.0,
            0.0,
        ),
    )

    point, first_t, _ = (
        line_intersection_3d(
            first,
            second,
        )
    )

    assert point == Node(
        0.0,
        0.0,
        0.0,
    )

    assert first_t == pytest.approx(
        -1.0
    )

    assert (
        classify_parameter(
            first_t
        )
        == "before_start"
    )


def test_interior_intersection_is_trim():
    assert (
        modification_kind(
            0.25
        )
        == "trim"
    )


def test_existing_endpoint_requires_no_modification():
    assert (
        modification_kind(
            0.0
        )
        == "none"
    )

    assert (
        modification_kind(
            1.0
        )
        == "none"
    )


def test_replace_end_preserves_profile_and_material():
    source = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    result = replace_member_endpoint(
        source,
        Node(
            500.0,
            0.0,
            0.0,
        ),
        "end",
    )

    assert result.start == source.start

    assert result.end == Node(
        500.0,
        0.0,
        0.0,
    )

    assert result.profile is source.profile
    assert result.material is source.material


def test_replace_start_preserves_opposite_endpoint():
    source = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    result = replace_member_endpoint(
        source,
        Node(
            -500.0,
            0.0,
            0.0,
        ),
        "start",
    )

    assert result.start == Node(
        -500.0,
        0.0,
        0.0,
    )

    assert result.end == source.end


def test_invalid_endpoint_name_is_rejected():
    source = member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Endpoint",
    ):
        replace_member_endpoint(
            source,
            Node(
                500.0,
                0.0,
                0.0,
            ),
            "middle",
        )
