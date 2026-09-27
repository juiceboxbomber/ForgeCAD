"""Bent-member Trim / Extend adapter and command regressions."""

import ast
from pathlib import Path
import sys
import types
from types import SimpleNamespace

import pytest


sys.modules.setdefault(
    "FreeCAD",
    types.ModuleType(
        "FreeCAD"
    ),
)

sys.modules.setdefault(
    "FreeCADGui",
    types.ModuleType(
        "FreeCADGui"
    ),
)

sys.modules.setdefault(
    "Part",
    types.ModuleType(
        "Part"
    ),
)

if "PySide" not in sys.modules:
    fake_pyside = types.ModuleType(
        "PySide"
    )
    fake_pyside.QtGui = SimpleNamespace(
        QDialog=object,
    )
    sys.modules[
        "PySide"
    ] = fake_pyside


from forgecad.fabrication import (
    Bend,
    BentMember,
    BentTube,
    Material,
    Member,
    Node,
    StraightRun,
    TubeProfile,
)
from forgecad.geometry import Vector3D
from forgecad.adapters.freecad import (
    member_trim_extend_adapter as module,
)


ROOT = Path(__file__).resolve().parents[1]

COMMAND = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "commands"
    / "trim_extend_member.py"
)


class FakeDocument:
    def __init__(
        self,
    ):
        self.recompute_count = 0

    def recompute(
        self,
    ):
        self.recompute_count += 1


class FakeBentProxy:
    def __init__(
        self,
    ):
        self.dirty = False

    def _is_multi_joint_derived_bend(
        self,
        obj,
    ):
        return False

    def _is_joint_derived_bend(
        self,
        obj,
    ):
        return True

    def mark_geometry_dirty(
        self,
    ):
        self.dirty = True


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def make_material():
    return Material(
        name="DOM Steel",
        density=7850.0,
        yield_strength=350.0,
    )


def make_bent_member():
    return BentMember(
        start=Node(
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            150.0,
            170.0,
            0.0,
        ),
        tube=BentTube(
            straight_runs=(
                StraightRun(
                    100.0
                ),
                StraightRun(
                    120.0
                ),
            ),
            bends=(
                Bend(
                    angle_degrees=90.0,
                    centerline_radius=50.0,
                ),
            ),
            profile=make_profile(),
            material=make_material(),
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


def make_target():
    return Member(
        start=Node(
            -40.0,
            -500.0,
            0.0,
        ),
        end=Node(
            -40.0,
            500.0,
            0.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )


def test_bent_source_is_updated_in_place(
    monkeypatch,
):
    document = FakeDocument()

    old_start = SimpleNamespace(
        Position=SimpleNamespace(
            x=0.0,
            y=0.0,
            z=0.0,
        )
    )

    old_end = SimpleNamespace(
        Position=SimpleNamespace(
            x=150.0,
            y=170.0,
            z=0.0,
        )
    )

    proxy = FakeBentProxy()

    source_object = SimpleNamespace(
        StartNode=old_start,
        EndNode=old_end,
        Proxy=proxy,
    )

    target_object = object()
    source_member = make_bent_member()
    target_member = make_target()

    def fake_reader(
        obj,
    ):
        if obj is source_object:
            return source_member

        if obj is target_object:
            return target_member

        raise AssertionError(
            "Unexpected object."
        )

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        fake_reader,
    )

    replacement_node = SimpleNamespace(
        Position=SimpleNamespace(
            x=-40.0,
            y=0.0,
            z=0.0,
        )
    )

    monkeypatch.setattr(
        module,
        "_get_or_create_node",
        lambda document, point: replacement_node,
    )

    removed_nodes = []

    monkeypatch.setattr(
        module,
        "remove_node_if_unused",
        lambda document, node: removed_nodes.append(
            node
        ),
    )

    events = []

    monkeypatch.setattr(
        module,
        "refresh_joint_topology",
        lambda document: events.append(
            "topology"
        ),
    )

    monkeypatch.setattr(
        module,
        "refresh_fabrication_for_document",
        lambda document: events.append(
            "fabrication"
        ),
    )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        lambda *args, **kwargs: pytest.fail(
            "Bent source must not be replaced by a straight member."
        ),
    )

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda *args, **kwargs: pytest.fail(
            "Bent source object must be preserved."
        ),
    )

    result = module.trim_extend_member_object(
        document,
        source_object,
        target_object,
        endpoint="start",
    )

    assert result[
        1
    ] is source_object
    assert result[
        3
    ] == "start"
    assert result[
        4
    ] == "extend"

    assert source_object.StartNode is replacement_node
    assert source_object.EndNode is old_end
    assert proxy.dirty is True
    assert removed_nodes == [
        old_start
    ]

    assert events == [
        "topology",
        "fabrication",
    ]


def _function_source(
    path,
    name,
):
    text = path.read_text(
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


def _class_method_source(
    path,
    class_name,
    method_name,
):
    text = path.read_text(
        encoding="utf-8"
    )
    tree = ast.parse(
        text
    )
    class_node = next(
        item
        for item in tree.body
        if isinstance(
            item,
            ast.ClassDef,
        )
        and item.name == class_name
    )
    method_node = next(
        item
        for item in class_node.body
        if isinstance(
            item,
            ast.FunctionDef,
        )
        and item.name == method_name
    )
    return ast.get_source_segment(
        text,
        method_node,
    )


def test_command_recognizes_bent_sources():
    source = _function_source(
        COMMAND,
        "is_forgecad_member",
    )
    assert "is_forgecad_bent_member" in source


def test_bent_source_waits_for_endpoint_click():
    source = _class_method_source(
        COMMAND,
        "InteractiveTrimExtendTool",
        "target_selected",
    )
    assert "is_forgecad_bent_member" in source
    assert "add_trim_click_callback" in source
    assert "Click the END" in source


def test_command_rejects_bent_target_in_phase_one():
    source = _class_method_source(
        COMMAND,
        "InteractiveTrimExtendTool",
        "target_selected",
    )
    assert "straight member as the target" in source
