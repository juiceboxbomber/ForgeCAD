"""Parametric cope target links must preserve bent endpoint tangents."""

import ast
from pathlib import Path
import sys
import types
from types import SimpleNamespace

import pytest

from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Material,
    Node,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import (
    Vector3D,
)


ROOT = Path(__file__).resolve().parents[1]
MEMBER_NOTCH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "member_notch.py"
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
    text = MEMBER_NOTCH.read_text(
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


PROFILE = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)

MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


def bent_domain():
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
        tube=BentTube(
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
        ),
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


def test_link_sync_uses_bent_local_tangent_not_start_end_chord(monkeypatch):
    target = SimpleNamespace(
        SourceLayoutID="",
        StartFabricationLayoutID="B-START",
        EndFabricationLayoutID="B-END",
        SourceLayoutLines=(),
        StartPoint=Vector(
            0.0,
            0.0,
            0.0,
        ),
        # Deliberately chord-like and wrong for the local start tangent.
        EndPoint=Vector(
            600.0,
            600.0,
            0.0,
        ),
    )

    fake_adapter = types.ModuleType(
        "forgecad.adapters.freecad.joint_inspector_adapter"
    )
    fake_adapter.structural_member_from_freecad_object = (
        lambda obj: bent_domain()
    )

    monkeypatch.setitem(
        sys.modules,
        "forgecad.adapters.freecad.joint_inspector_adapter",
        fake_adapter,
    )

    obj = SimpleNamespace(
        StartPoint=Vector(
            0.0,
            0.0,
            0.0,
        ),
        EndPoint=Vector(
            -500.0,
            200.0,
            0.0,
        ),
        StartCopeEnabled=True,
        StartCopeTargetMember=target,
        StartCopeThroughStart=Vector(),
        StartCopeThroughEnd=Vector(),
        EndCopeEnabled=False,
        EndCopeTargetMember=None,
        StartCope2Enabled=False,
        StartCope2TargetMember=None,
        EndCope2Enabled=False,
        EndCope2TargetMember=None,
        StartCope3Enabled=False,
        StartCope3TargetMember=None,
        EndCope3Enabled=False,
        EndCope3TargetMember=None,
    )

    namespace = {
        "FreeCAD": SimpleNamespace(
            Vector=Vector
        ),
        "ensure_notch_properties": lambda target: None,
    }

    exec(
        function_source(
            "sync_cope_axes_from_target_members"
        ),
        namespace,
    )

    changed = namespace[
        "sync_cope_axes_from_target_members"
    ](
        obj
    )

    assert changed == 1

    assert xyz(
        obj.StartCopeThroughStart
    ) == pytest.approx(
        (
            0.0,
            0.0,
            0.0,
        )
    )

    assert xyz(
        obj.StartCopeThroughEnd
    ) == pytest.approx(
        (
            500.0,
            0.0,
            0.0,
        ),
        abs=1e-7,
    )
