"""Tests for Mirror Members principal-plane integration."""

import sys
import types
from types import SimpleNamespace


class FakeQDialog:
    Accepted = 1


class FakeQMessageBox:
    @staticmethod
    def warning(
        *args,
        **kwargs,
    ):
        return None


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)
fake_freecad_gui.Selection = SimpleNamespace(
    getSelection=lambda: [],
    clearSelection=lambda: None,
    addSelection=lambda obj: None,
)
fake_freecad_gui.addCommand = lambda *args, **kwargs: None
fake_freecad_gui.getMainWindow = lambda: None

fake_part = types.ModuleType(
    "Part"
)

fake_pyside = types.ModuleType(
    "PySide"
)
fake_pyside.QtGui = SimpleNamespace(
    QDialog=FakeQDialog,
    QMessageBox=FakeQMessageBox,
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


from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.adapters.freecad.commands import (
    mirror_members as module,
)


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


def make_member():
    return Member(
        start=Node(
            100.0,
            200.0,
            300.0,
        ),
        end=Node(
            500.0,
            600.0,
            700.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )


def test_plane_member_creation_uses_selected_plane(
    monkeypatch,
):
    source = make_member()

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: source,
    )

    created_points = []

    fake_draw_module = types.ModuleType(
        "forgecad.adapters.freecad.commands.draw_member_interactive"
    )

    def fake_get_or_create_node(
        document,
        point,
    ):
        created_points.append(
            point
        )
        return SimpleNamespace(
            Position=point
        )

    fake_draw_module.get_or_create_node = (
        fake_get_or_create_node
    )

    monkeypatch.setitem(
        sys.modules,
        (
            "forgecad.adapters.freecad.commands."
            "draw_member_interactive"
        ),
        fake_draw_module,
    )

    captured = {}

    def fake_create(
        document,
        start_node,
        end_node,
        profile=None,
        material=None,
    ):
        captured["profile"] = profile
        captured["material"] = material

        return (
            object(),
            "mirror",
        )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        fake_create,
    )

    result = (
        module.mirror_member_object_across_plane(
            object(),
            object(),
            "XZ",
        )
    )

    assert result == "mirror"

    assert created_points[0].x == 100.0
    assert created_points[0].y == -200.0
    assert created_points[0].z == 300.0

    assert created_points[1].x == 500.0
    assert created_points[1].y == -600.0
    assert created_points[1].z == 700.0

    assert captured["profile"] is source.profile
    assert captured["material"] is source.material


def test_plane_batch_mirrors_every_source_member(
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        module,
        "mirror_member_object_across_plane",
        lambda document, obj, plane: (
            calls.append(
                (
                    obj,
                    plane,
                )
            )
            or f"mirror-{obj}"
        ),
    )

    result = (
        module.mirror_member_objects_across_plane(
            object(),
            [
                "M001",
                "M002",
                "M003",
            ],
            "YZ",
        )
    )

    assert calls == [
        (
            "M001",
            "YZ",
        ),
        (
            "M002",
            "YZ",
        ),
        (
            "M003",
            "YZ",
        ),
    ]

    assert result == (
        "mirror-M001",
        "mirror-M002",
        "mirror-M003",
    )


def test_dialog_plane_modes_map_to_expected_plane_names():
    plane_by_mode = {
        module.MirrorReferenceDialog.XY_PLANE: "XY",
        module.MirrorReferenceDialog.XZ_PLANE: "XZ",
        module.MirrorReferenceDialog.YZ_PLANE: "YZ",
    }

    assert (
        plane_by_mode[
            module.MirrorReferenceDialog.XY_PLANE
        ]
        == "XY"
    )

    assert (
        plane_by_mode[
            module.MirrorReferenceDialog.XZ_PLANE
        ]
        == "XZ"
    )

    assert (
        plane_by_mode[
            module.MirrorReferenceDialog.YZ_PLANE
        ]
        == "YZ"
    )
