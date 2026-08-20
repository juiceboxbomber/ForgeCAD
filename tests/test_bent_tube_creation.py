import pytest

from forgecad.fabrication import (
    Material,
    TubeProfile,
)
from forgecad.services.bent_tube_creation import (
    BendInput,
    BentTubeInput,
    create_bent_tube,
)


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def make_material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def test_bent_tube_input_requires_one_more_run_than_bends():
    with pytest.raises(
        ValueError,
        match="one more straight run",
    ):
        BentTubeInput(
            name="Main Hoop",
            run_lengths=(
                500.0,
            ),
            bends=(
                BendInput(
                    angle_degrees=90.0,
                    centerline_radius=100.0,
                ),
            ),
        )


def test_bent_tube_input_rejects_empty_name():
    with pytest.raises(
        ValueError,
        match="name cannot be empty",
    ):
        BentTubeInput(
            name="   ",
            run_lengths=(
                500.0,
            ),
            bends=(),
        )


def test_bent_tube_input_rejects_nonpositive_run():
    with pytest.raises(
        ValueError,
        match="must be positive",
    ):
        BentTubeInput(
            name="Main Hoop",
            run_lengths=(
                500.0,
                0.0,
            ),
            bends=(
                BendInput(
                    angle_degrees=90.0,
                    centerline_radius=100.0,
                ),
            ),
        )


def test_create_single_bend_tube():
    definition = BentTubeInput(
        name="Main Hoop",
        run_lengths=(
            500.0,
            750.0,
        ),
        bends=(
            BendInput(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
        ),
    )

    tube = create_bent_tube(
        definition,
        make_profile(),
        make_material(),
    )

    assert tube.bend_count == 1

    assert tuple(
        run.length_mm
        for run in tube.straight_runs
    ) == (
        500.0,
        750.0,
    )

    assert tube.bends[0].angle_degrees == 90.0
    assert tube.bends[0].centerline_radius == 100.0


def test_create_multi_bend_tube_preserves_rotation():
    definition = BentTubeInput(
        name="A-Pillar",
        run_lengths=(
            400.0,
            500.0,
            600.0,
        ),
        bends=(
            BendInput(
                angle_degrees=75.0,
                centerline_radius=100.0,
                rotation_degrees=0.0,
            ),
            BendInput(
                angle_degrees=45.0,
                centerline_radius=125.0,
                rotation_degrees=90.0,
            ),
        ),
    )

    tube = create_bent_tube(
        definition,
        make_profile(),
        make_material(),
    )

    assert tube.bend_count == 2
    assert tube.bends[1].rotation_degrees == 90.0
    assert tube.bends[1].centerline_radius == 125.0
    