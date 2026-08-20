"""Tests for the FreeCAD bent-tube geometry adapter."""

import sys
import types

import pytest


class FakeVector:
    """Minimal FreeCAD.Vector replacement."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __sub__(
        self,
        other,
    ):
        return FakeVector(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z,
        )

    def __add__(
        self,
        other,
    ):
        return FakeVector(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
        )


class FakeRotation:
    """Enough rotation behavior for the adapter midpoint calculation."""

    def __init__(
        self,
        axis,
        angle_degrees,
    ):
        self.axis = axis
        self.angle_degrees = float(
            angle_degrees
        )

    def multVec(
        self,
        vector,
    ):
        # These adapter tests exercise XY-plane arcs around +Z.
        if (
            abs(self.axis.x) < 1e-9
            and abs(self.axis.y) < 1e-9
            and abs(abs(self.axis.z) - 1.0) < 1e-9
        ):
            import math

            angle = math.radians(
                self.angle_degrees
                * (
                    1.0
                    if self.axis.z >= 0.0
                    else -1.0
                )
            )

            return FakeVector(
                vector.x * math.cos(angle)
                - vector.y * math.sin(angle),
                vector.x * math.sin(angle)
                + vector.y * math.cos(angle),
                vector.z,
            )

        raise AssertionError(
            "Unexpected fake rotation axis."
        )


class FakeEdge:
    def __init__(
        self,
        kind,
        data,
    ):
        self.kind = kind
        self.data = data


class FakeArc:
    def __init__(
        self,
        start,
        midpoint,
        end,
    ):
        self.start = start
        self.midpoint = midpoint
        self.end = end

    def toShape(
        self,
    ):
        return FakeEdge(
            "arc",
            (
                self.start,
                self.midpoint,
                self.end,
            ),
        )


class FakeSolid:
    def __init__(
        self,
        name,
    ):
        self.name = name

    def cut(
        self,
        other,
    ):
        return (
            "cut",
            self,
            other,
        )


class FakeWire:
    def __init__(
        self,
        edges,
    ):
        self.edges = list(
            edges
        )
        self.pipe_calls = []

    def makePipeShell(
        self,
        profiles,
        make_solid,
        is_frenet,
    ):
        self.pipe_calls.append(
            (
                profiles,
                make_solid,
                is_frenet,
            )
        )

        return FakeSolid(
            f"sweep-{len(self.pipe_calls)}"
        )


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.Vector = FakeVector
fake_freecad.Rotation = FakeRotation

fake_part = types.ModuleType(
    "Part"
)
fake_part.Arc = FakeArc
fake_part.Wire = FakeWire
fake_part.makeLine = (
    lambda start, end: FakeEdge(
        "line",
        (
            start,
            end,
        ),
    )
)
fake_part.makeCircle = (
    lambda radius, point, direction: FakeEdge(
        "circle",
        (
            float(radius),
            point,
            direction,
        ),
    )
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "Part"
] = fake_part


from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import (
    Point3D,
    Vector3D,
)
from forgecad.services.bent_tube_path import (
    CircularArcPathSegment,
    StraightPathSegment,
    build_bent_tube_centerline,
)
from forgecad.adapters.freecad.bent_tube_geometry import (
    build_bent_tube_shape,
    build_centerline_edge,
    build_centerline_wire,
    point_vector,
    vector3d_vector,
)


def _material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def _profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def _tube():
    return BentTube(
        straight_runs=(
            StraightRun(500.0),
            StraightRun(750.0),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


def test_point_and_vector_conversion():
    point = point_vector(
        Point3D(
            1.0,
            2.0,
            3.0,
        )
    )

    vector = vector3d_vector(
        Vector3D(
            4.0,
            5.0,
            6.0,
        )
    )

    assert (
        point.x,
        point.y,
        point.z,
    ) == (
        1.0,
        2.0,
        3.0,
    )

    assert (
        vector.x,
        vector.y,
        vector.z,
    ) == (
        4.0,
        5.0,
        6.0,
    )


def test_straight_segment_builds_line_edge():
    segment = StraightPathSegment(
        start=Point3D(
            0.0,
            0.0,
            0.0,
        ),
        end=Point3D(
            100.0,
            0.0,
            0.0,
        ),
    )

    edge = build_centerline_edge(
        segment
    )

    assert edge.kind == "line"
    assert edge.data[0].x == pytest.approx(
        0.0
    )
    assert edge.data[1].x == pytest.approx(
        100.0
    )


def test_arc_segment_builds_three_point_arc_edge():
    centerline = build_bent_tube_centerline(
        _tube()
    )

    arc_segment = centerline.segments[
        1
    ]

    assert isinstance(
        arc_segment,
        CircularArcPathSegment,
    )

    edge = build_centerline_edge(
        arc_segment
    )

    assert edge.kind == "arc"

    start, midpoint, end = (
        edge.data
    )

    assert start.x == pytest.approx(
        500.0
    )
    assert start.y == pytest.approx(
        0.0
    )

    assert midpoint.x == pytest.approx(
        570.710678,
        abs=1e-6,
    )
    assert midpoint.y == pytest.approx(
        29.289322,
        abs=1e-6,
    )

    assert end.x == pytest.approx(
        600.0
    )
    assert end.y == pytest.approx(
        100.0
    )


def test_centerline_wire_preserves_segment_order():
    centerline = build_bent_tube_centerline(
        _tube()
    )

    wire = build_centerline_wire(
        centerline
    )

    assert [
        edge.kind
        for edge in wire.edges
    ] == [
        "line",
        "arc",
        "line",
    ]


def test_bent_tube_shape_sweeps_outer_and_inner_profiles():
    shape, centerline = build_bent_tube_shape(
        _tube()
    )

    assert shape[0] == "cut"

    outer_solid = shape[1]
    inner_solid = shape[2]

    assert isinstance(
        outer_solid,
        FakeSolid,
    )
    assert isinstance(
        inner_solid,
        FakeSolid,
    )

    assert centerline.segment_count == 3


def test_unsupported_segment_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="Unsupported",
    ):
        build_centerline_edge(
            object()
        )
