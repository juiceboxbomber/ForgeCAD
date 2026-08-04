import pytest

from forgecad.geometry import Vector3D


def test_vector_magnitude():
    vector = Vector3D(3.0, 4.0, 12.0)

    assert vector.magnitude == pytest.approx(13.0)


def test_normalization():
    vector = Vector3D(10.0, 0.0, 0.0)

    unit = vector.normalized()

    assert unit.x == pytest.approx(1.0)
    assert unit.y == 0.0
    assert unit.z == 0.0


def test_dot_product():
    a = Vector3D(1, 2, 3)
    b = Vector3D(4, 5, 6)

    assert a.dot(b) == 32


def test_zero_vector_normalization():
    with pytest.raises(ValueError):
        Vector3D(0, 0, 0).normalized()
        