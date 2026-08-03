import pytest

from forgecad.fabrication.material import Material


def test_material_creation():
    steel = Material(
        name="4130 Chromoly",
        density=7.85e-6,
        yield_strength=435,
        ultimate_strength=670,
        elastic_modulus=205000,
    )

    assert steel.name == "4130 Chromoly"
    assert steel.yield_strength == 435


def test_empty_name_is_invalid():
    with pytest.raises(ValueError):
        Material(
            name="",
            density=7.85e-6,
            yield_strength=435,
            ultimate_strength=670,
            elastic_modulus=205000,
        )


def test_invalid_strength_relationship():
    with pytest.raises(ValueError):
        Material(
            name="Bad Material",
            density=7.85e-6,
            yield_strength=700,
            ultimate_strength=500,
            elastic_modulus=205000,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("density", 0),
        ("yield_strength", 0),
        ("ultimate_strength", 0),
        ("elastic_modulus", 0),
    ],
)
def test_invalid_values(field, value):
    kwargs = {
        "name": "Test",
        "density": 7.85e-6,
        "yield_strength": 435,
        "ultimate_strength": 670,
        "elastic_modulus": 205000,
    }

    kwargs[field] = value

    with pytest.raises(ValueError):
        Material(**kwargs)
        