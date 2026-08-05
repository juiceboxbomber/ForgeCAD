import pytest

from forgecad import FrameLayout, LayoutLine
from forgecad.geometry import Point3D


def test_layout_line_length():
    line = LayoutLine(
        start=Point3D(0, 0, 0),
        end=Point3D(300, 400, 0),
    )

    assert line.length == pytest.approx(500)


def test_zero_length_line_is_rejected():
    point = Point3D(10, 20, 30)

    with pytest.raises(ValueError):
        LayoutLine(point, point)


def test_add_layout_line():
    layout = FrameLayout()
    line = LayoutLine(
        Point3D(0, 0, 0),
        Point3D(1000, 0, 0),
    )

    layout.add_line(line)

    assert layout.line_count == 1
    assert layout.lines[0] is line


def test_duplicate_line_is_not_added():
    layout = FrameLayout()
    line = LayoutLine(
        Point3D(0, 0, 0),
        Point3D(1000, 0, 0),
    )

    layout.add_line(line)
    layout.add_line(line)

    assert layout.line_count == 1


def test_layout_returns_unique_points():
    a = Point3D(0, 0, 0)
    b = Point3D(1000, 0, 0)
    c = Point3D(1000, 600, 0)

    layout = FrameLayout(
        lines=[
            LayoutLine(a, b),
            LayoutLine(b, c),
        ]
    )

    assert layout.points == (a, b, c)
    