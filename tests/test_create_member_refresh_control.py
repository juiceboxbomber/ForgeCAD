"""Tests for deferred refresh during compound member edits."""

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


fake_pyside.QtGui = SimpleNamespace(
    QDialog=FakeQDialog,
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
    def render_tube(
        self,
        document,
        member,
        member_id="",
        source_layout_id="",
    ):
        return SimpleNamespace(
            MemberID=member_id,
            SourceLayoutID=source_layout_id,
        )


def install_common_stubs(
    monkeypatch,
):
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

    monkeypatch.setattr(
        module,
        "initialize_project_tree",
        lambda document: {
            "Layout": FakeGroup(),
            "Frame": FakeGroup(),
        },
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
        FakeRenderer,
    )

    monkeypatch.setattr(
        module,
        "ensure_member_node_links",
        lambda *args, **kwargs: None,
    )


def test_default_creation_still_refreshes(
    monkeypatch,
):
    install_common_stubs(
        monkeypatch
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

    module.create_member_between_nodes(
        FakeDocument(),
        FakeNode(
            0,
            0,
            0,
        ),
        FakeNode(
            1000,
            0,
            0,
        ),
    )

    assert events == [
        "topology",
        "fabrication",
    ]


def test_refresh_can_be_deferred_for_compound_edit(
    monkeypatch,
):
    install_common_stubs(
        monkeypatch
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

    module.create_member_between_nodes(
        FakeDocument(),
        FakeNode(
            0,
            0,
            0,
        ),
        FakeNode(
            1000,
            0,
            0,
        ),
        refresh=False,
    )

    assert events == []
