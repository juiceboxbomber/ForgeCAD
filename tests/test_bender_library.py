"""Tests for ForgeCAD bender tooling libraries."""

import pytest

from forgecad.fabrication import (
    BenderLibrary,
    BenderTooling,
)


def _tooling(
    name,
    radius,
):
    return BenderTooling(
        name=name,
        centerline_radius_mm=radius,
    )


def test_first_tooling_becomes_active():
    library = BenderLibrary()

    library.add(
        _tooling(
            "100 mm CLR",
            100.0,
        )
    )

    assert library.active_name == "100 mm CLR"
    assert (
        library.active_tooling
        is library.get(
            "100 mm CLR"
        )
    )


def test_library_preserves_tooling_order():
    library = BenderLibrary()

    library.add(
        _tooling(
            "100 mm CLR",
            100.0,
        )
    )
    library.add(
        _tooling(
            "150 mm CLR",
            150.0,
        )
    )

    assert library.names == (
        "100 mm CLR",
        "150 mm CLR",
    )


def test_library_can_change_active_tooling():
    library = BenderLibrary()

    library.add(
        _tooling(
            "100 mm CLR",
            100.0,
        )
    )
    library.add(
        _tooling(
            "150 mm CLR",
            150.0,
        )
    )

    library.set_active(
        "150 mm CLR"
    )

    assert library.active_name == "150 mm CLR"
    assert (
        library.active_tooling.centerline_radius_mm
        == pytest.approx(150.0)
    )


def test_duplicate_tooling_name_is_rejected():
    library = BenderLibrary()

    library.add(
        _tooling(
            "Main Die",
            100.0,
        )
    )

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        library.add(
            _tooling(
                "Main Die",
                125.0,
            )
        )


def test_unknown_tooling_name_is_rejected():
    library = BenderLibrary()

    with pytest.raises(
        KeyError,
    ):
        library.get(
            "Missing"
        )


def test_remove_active_tooling_selects_next_available():
    library = BenderLibrary()

    library.add(
        _tooling(
            "100 mm CLR",
            100.0,
        )
    )
    library.add(
        _tooling(
            "150 mm CLR",
            150.0,
        )
    )

    removed = library.remove(
        "100 mm CLR"
    )

    assert removed.name == "100 mm CLR"
    assert library.active_name == "150 mm CLR"


def test_compatible_tooling_filters_by_centerline_radius():
    library = BenderLibrary()

    library.add(
        _tooling(
            "100 mm A",
            100.0,
        )
    )
    library.add(
        _tooling(
            "100 mm B",
            100.0005,
        )
    )
    library.add(
        _tooling(
            "150 mm",
            150.0,
        )
    )

    compatible = library.compatible_tooling(
        100.0,
        tolerance_mm=0.001,
    )

    assert [
        tooling.name
        for tooling in compatible
    ] == [
        "100 mm A",
        "100 mm B",
    ]


def test_compatible_tooling_requires_positive_radius():
    library = BenderLibrary()

    with pytest.raises(
        ValueError,
        match="Centerline radius",
    ):
        library.compatible_tooling(
            0.0
        )


def test_add_rejects_wrong_type():
    library = BenderLibrary()

    with pytest.raises(
        TypeError,
        match="BenderTooling",
    ):
        library.add(
            object()
        )
