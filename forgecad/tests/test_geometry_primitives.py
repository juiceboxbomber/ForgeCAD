import pytest

from forgecad.geometry.primitives import LineSegment, Point3D


def test_point_creation():
    point = Point3D(1, 2, 3)

    assert point.x == 1
    assert point.y == 2
    assert point.z == 3


def test_line_length():
    line = LineSegment(
        Point3D(0, 0, 0),
        Point3D(300, 400, 0),
    )

    assert line.length == pytest.approx(500)
    