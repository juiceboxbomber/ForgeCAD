"""Bent-member Split Member adapter tests."""

import sys
import types
from types import SimpleNamespace

import pytest


fake_freecad = types.ModuleType("FreeCAD")
fake_freecad.Vector = lambda x, y, z: SimpleNamespace(
    x=float(x),
    y=float(y),
    z=float(z),
)

sys.modules["FreeCAD"] = fake_freecad
sys.modules["FreeCADGui"] = types.ModuleType("FreeCADGui")
sys.modules["Part"] = types.ModuleType("Part")

fake_pyside = types.ModuleType("PySide")
fake_pyside.QtGui = SimpleNamespace(
    QDialog=object,
    QMessageBox=SimpleNamespace(
        warning=lambda *args, **kwargs: None,
    ),
)
sys.modules["PySide"] = fake_pyside


from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import Point3D
from forgecad.adapters.freecad import member_split_adapter as module


class FakeGroup:
    def __init__(self, objects=()):
        self.Group = list(objects)

    def addObject(self, obj):
        if obj not in self.Group:
            self.Group.append(obj)

    def removeObject(self, obj):
        if obj in self.Group:
            self.Group.remove(obj)


class FakeDocument:
    def __init__(self):
        self.removed = []
        self.recompute_count = 0

    def removeObject(self, name):
        self.removed.append(name)

    def recompute(self):
        self.recompute_count += 1


def profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def material():
    return Material(
        name="DOM Steel",
        density=7850.0,
        yield_strength=350.0,
    )


def tube():
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
        profile=profile(),
        material=material(),
    )


def vector(x, y, z):
    return SimpleNamespace(
        x=float(x),
        y=float(y),
        z=float(z),
    )


def layout(name, layout_id, start, end):
    return SimpleNamespace(
        Name=name,
        LayoutID=layout_id,
        StartPoint=vector(*start),
        EndPoint=vector(*end),
        ViewObject=SimpleNamespace(
            Visibility=False,
        ),
    )


def test_second_split_frame_uses_local_tangent_and_previous_bend_normal():
    second_start, direction, normal, segment = (
        module._second_split_frame(
            tube(),
            1,
            Point3D(
                600.0,
                475.0,
                0.0,
            ),
            Point3D(
                0.0,
                0.0,
                0.0,
            ),
            module.Vector3D(
                1.0,
                0.0,
                0.0,
            ),
            module.Vector3D(
                0.0,
                0.0,
                1.0,
            ),
        )
    )

    assert second_start == Point3D(
        600.0,
        475.0,
        0.0,
    )
    assert direction.x == pytest.approx(0.0)
    assert direction.y == pytest.approx(1.0)
    assert direction.z == pytest.approx(0.0)
    assert normal.z == pytest.approx(1.0)
    assert segment.start.x == pytest.approx(600.0)
    assert segment.start.y == pytest.approx(100.0)


def test_split_layout_preserves_original_id_on_end_side_for_last_run(
    monkeypatch,
):
    document = FakeDocument()
    group = FakeGroup()
    tree = {
        "Layout": group,
    }

    source = layout(
        "LayoutOriginal",
        "layout-original",
        (600.0, 100.0, 0.0),
        (600.0, 850.0, 0.0),
    )
    group.addObject(source)

    created = []

    def fake_create(document, line):
        obj = layout(
            f"Layout{len(created) + 1}",
            f"layout-new-{len(created) + 1}",
            (
                line.start.x,
                line.start.y,
                line.start.z,
            ),
            (
                line.end.x,
                line.end.y,
                line.end.z,
            ),
        )
        created.append(obj)
        return obj

    monkeypatch.setattr(
        module,
        "initialize_project_tree",
        lambda document: tree,
    )
    monkeypatch.setattr(
        module,
        "create_layout_line_object",
        fake_create,
    )
    monkeypatch.setattr(
        module,
        "ensure_layout_id",
        lambda obj: obj.LayoutID,
    )

    first, second = (
        module._create_split_source_layouts(
            document,
            source,
            Point3D(
                600.0,
                475.0,
                0.0,
            ),
            Point3D(
                600.0,
                100.0,
                0.0,
            ),
            Point3D(
                600.0,
                850.0,
                0.0,
            ),
            preserve_original_id_on_second=True,
        )
    )

    assert first.LayoutID != "layout-original"
    assert second.LayoutID == "layout-original"
    assert source.Name in document.removed


def test_split_member_object_dispatches_bent_members(
    monkeypatch,
):
    sentinel = object()
    source = object()

    monkeypatch.setattr(
        module,
        "is_forgecad_bent_member",
        lambda obj: obj is source,
    )
    monkeypatch.setattr(
        module,
        "split_bent_member_object",
        lambda document, member_object, split_point: sentinel,
    )

    assert (
        module.split_member_object(
            object(),
            source,
            Point3D(
                10.0,
                0.0,
                0.0,
            ),
        )
        is sentinel
    )


def test_resolved_bent_definition_solves_joint_derived_path_before_reading():
    source_tube = tube()

    obj = SimpleNamespace(
        StartPoint=vector(
            0.0,
            0.0,
            0.0,
        ),
        InitialDirection=vector(
            1.0,
            0.0,
            0.0,
        ),
        InitialBendNormal=vector(
            0.0,
            0.0,
            1.0,
        ),
    )

    calls = []

    class Proxy:
        def update_shape(
            self,
            member_object,
        ):
            calls.append(
                "update"
            )

            member_object.StartPoint = vector(
                10.0,
                20.0,
                0.0,
            )

            member_object.InitialDirection = vector(
                0.6,
                0.8,
                0.0,
            )

            member_object.InitialBendNormal = vector(
                0.0,
                0.0,
                -1.0,
            )

        def _tube_from_properties(
            self,
            member_object,
        ):
            calls.append(
                "tube"
            )
            return source_tube

    obj.Proxy = Proxy()

    (
        resolved_tube,
        start_point,
        direction,
        normal,
    ) = module._resolved_bent_definition(
        obj
    )

    assert calls == [
        "update",
        "tube",
    ]

    assert resolved_tube is source_tube

    assert start_point == Point3D(
        10.0,
        20.0,
        0.0,
    )

    assert direction.x == pytest.approx(
        0.6
    )
    assert direction.y == pytest.approx(
        0.8
    )

    assert normal.z == pytest.approx(
        -1.0
    )
