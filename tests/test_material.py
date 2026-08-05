import pytest

from forgecad.fabrication import Material


def test_material_creation():
    steel = Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )

    assert steel.name == "A513 Type 5 DOM"
    assert steel.density == 7850.0
    assert steel.yield_strength == 350.0


def test_density_must_be_positive():
    with pytest.raises(ValueError):
        Material(
            name="Steel",
            density=0.0,
            yield_strength=350.0,
        )


def test_yield_strength_must_be_positive():
    with pytest.raises(ValueError):
        Material(
            name="Steel",
            density=7850.0,
            yield_strength=0.0,
        )
        