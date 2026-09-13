"""Tests for explicit profile/material member creation."""

import sys
import types
from types import SimpleNamespace


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)
fake_part = types.ModuleType(
    "Part"
)
fake_pyside = types.ModuleType(
    "PySide"
)

class FakeQDialog:
    pass


fake_pyside.QtGui = (
    SimpleNamespace(
        QDialog=FakeQDialog,
    )
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "FreeCADGui"
] = fake_freecad_gui
sys.modules[
    "Part"
] = fake_part
sys.modules[
    "PySide"
] = fake_pyside


from forgecad.adapters.freecad.commands import (
    create_member_between_nodes as module,
)


class FakePosition:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


class FakeNode:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.Position = FakePosition(
            x,
            y,
            z,
        )
        self.NodeID = "N001"


class FakeGroup:
    def __init__(self):
        self.Group = []

    def addObject(
        self,
        obj,
    ):
        self.Group.append(
            obj
        )


class FakeDocument:
    def recompute(self):
        pass


class FakeRenderer:
    def __init__(self):
        self.last_member = None

    def render_tube(
        self,
        document,
        member,
        member_id="",
        source_layout_id="",
    ):
        self.last_member = member

        return SimpleNamespace(
            MemberID=member_id,
            SourceLayoutID=source_layout_id,
        )


def make_groups():
    return {
        "Layout": FakeGroup(),
        "Frame": FakeGroup(),
    }


def test_explicit_profile_and_material_are_preserved(
    monkeypatch,
):
    document = FakeDocument()

    start = FakeNode(
        0,
        0,
        0,
    )
    end = FakeNode(
        1000,
        0,
        0,
    )

    explicit_profile = object()
    explicit_material = object()

    renderer = FakeRenderer()

    monkeypatch.setattr(
        module,
        "project_from_document",
        lambda document: SimpleNamespace(
            tube_library=SimpleNamespace(
                active_profile=object()
            ),
            default_material=object(),
        ),
    )

    groups = make_groups()

    monkeypatch.setattr(
        module,
        "initialize_project_tree",
        lambda document: groups,
    )

    monkeypatch.setattr(
        module,
        "ensure_layout_object_between_nodes",
        lambda *args, **kwargs: SimpleNamespace(),
    )

    monkeypatch.setattr(
        module,
        "ensure_layout_id",
        lambda obj: "L001",
    )

    monkeypatch.setattr(
        module,
        "FrameRenderer",
        lambda: renderer,
    )

    monkeypatch.setattr(
        module,
        "ensure_member_node_links",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        module,
        "refresh_joint_topology",
        lambda document: None,
    )

    monkeypatch.setattr(
        module,
        "refresh_fabrication_for_document",
        lambda document: None,
    )

    module.create_member_between_nodes(
        document,
        start,
        end,
        profile=explicit_profile,
        material=explicit_material,
    )

    assert (
        renderer.last_member.profile
        is explicit_profile
    )

    assert (
        renderer.last_member.material
        is explicit_material
    )


def test_omitted_profile_and_material_use_project_defaults(
    monkeypatch,
):
    document = FakeDocument()

    start = FakeNode(
        0,
        0,
        0,
    )
    end = FakeNode(
        1000,
        0,
        0,
    )

    default_profile = object()
    default_material = object()

    renderer = FakeRenderer()

    monkeypatch.setattr(
        module,
        "project_from_document",
        lambda document: SimpleNamespace(
            tube_library=SimpleNamespace(
                active_profile=default_profile
            ),
            default_material=default_material,
        ),
    )

    groups = make_groups()

    monkeypatch.setattr(
        module,
        "initialize_project_tree",
        lambda document: groups,
    )

    monkeypatch.setattr(
        module,
        "ensure_layout_object_between_nodes",
        lambda *args, **kwargs: SimpleNamespace(),
    )

    monkeypatch.setattr(
        module,
        "ensure_layout_id",
        lambda obj: "L001",
    )

    monkeypatch.setattr(
        module,
        "FrameRenderer",
        lambda: renderer,
    )

    monkeypatch.setattr(
        module,
        "ensure_member_node_links",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        module,
        "refresh_joint_topology",
        lambda document: None,
    )

    monkeypatch.setattr(
        module,
        "refresh_fabrication_for_document",
        lambda document: None,
    )

    module.create_member_between_nodes(
        document,
        start,
        end,
    )

    assert (
        renderer.last_member.profile
        is default_profile
    )

    assert (
        renderer.last_member.material
        is default_material
    )
