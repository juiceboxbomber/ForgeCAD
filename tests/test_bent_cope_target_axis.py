"""Bent cope targets must use local endpoint tangents rather than chords."""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Joint,
    Material,
    Node,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import (
    Vector3D,
)


ROOT = Path(__file__).resolve().parents[1]
RENDERER = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "renderer.py"
)


class Vector:
    def __init__(
        self,
        x=0.0,
        y=0.0,
        z=0.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


def function_source(name):
    text = RENDERER.read_text(
        encoding="utf-8"
    )
    tree = ast.parse(
        text
    )
    node = next(
        item
        for item in tree.body
        if isinstance(
            item,
            ast.FunctionDef,
        )
        and item.name == name
    )
    return ast.get_source_segment(
        text,
        node,
    )


def target_axis(specification):
    namespace = {
        "FreeCAD": SimpleNamespace(
            Vector=Vector
        ),
        "node_vector": lambda node: Vector(
            node.x,
            node.y,
            node.z,
        ),
    }

    exec(
        function_source(
            "target_axis_for_cope_specification"
        ),
        namespace,
    )

    return namespace[
        "target_axis_for_cope_specification"
    ](
        specification
    )


PROFILE = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)

MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


def bent_member():
    tube = BentTube(
        straight_runs=(
            StraightRun(
                500.0
            ),
            StraightRun(
                500.0
            ),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
            ),
        ),
        profile=PROFILE,
        material=MATERIAL,
    )

    return BentMember(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            600.0,
            600.0,
            0.0,
        ),
        tube=tube,
        initial_direction=Vector3D(
            1.0,
            0.0,
            0.0,
        ),
        initial_bend_normal=Vector3D(
            0.0,
            0.0,
            1.0,
        ),
    )


def xyz(value):
    return (
        value.x,
        value.y,
        value.z,
    )


def test_bent_start_target_axis_uses_first_run_not_chord():
    bent = bent_member()
    joint = Joint(
        node=bent.start,
        members=[
            bent
        ],
    )

    start, end = target_axis(
        SimpleNamespace(
            target_member=bent,
            joint=joint,
        )
    )

    assert xyz(
        start
    ) == pytest.approx(
        (
            0.0,
            0.0,
            0.0,
        )
    )

    assert xyz(
        end
    ) == pytest.approx(
        (
            500.0,
            0.0,
            0.0,
        ),
        abs=1e-7,
    )

    # The overall bent-member chord would point toward (600, 600, 0).
    assert end.y == pytest.approx(
        0.0,
        abs=1e-7,
    )


def test_bent_end_target_axis_uses_last_run_inward_not_chord():
    bent = bent_member()
    joint = Joint(
        node=bent.end,
        members=[
            bent
        ],
    )

    start, end = target_axis(
        SimpleNamespace(
            target_member=bent,
            joint=joint,
        )
    )

    assert xyz(
        start
    ) == pytest.approx(
        (
            600.0,
            600.0,
            0.0,
        ),
        abs=1e-7,
    )

    assert xyz(
        end
    ) == pytest.approx(
        (
            600.0,
            100.0,
            0.0,
        ),
        abs=1e-7,
    )

    assert end.x == pytest.approx(
        600.0,
        abs=1e-7,
    )
