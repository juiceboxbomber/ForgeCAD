"""Tests for automatic continuous-member handling during Mirror Members."""

import sys
import types
from types import SimpleNamespace


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


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
fake_freecad.Vector = FakeVector
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)
fake_freecad_gui.Selection = SimpleNamespace(
    getSelection=lambda: [],
    clearSelection=lambda: None,
    addSelection=lambda obj: None,
)
fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)
fake_freecad_gui.getMainWindow = (
    lambda: None
)

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


def domain_member(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=profile(),
        material=material(),
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


def test_collinear_source_and_mirror_extend_original_member(
    monkeypatch,
):
    document = FakeDocument()

    center_node = object()
    source_outer_node = object()
    mirror_outer_node = object()

    source = SimpleNamespace(
        MemberID="M001",
        SourceLayoutID="L001",
        StartNode=center_node,
        EndNode=source_outer_node,
        StartPoint=FakeVector(
            0.0,
            0.0,
            0.0,
        ),
        EndPoint=FakeVector(
            500.0,
            0.0,
            0.0,
        ),
        touch=lambda: None,
    )

    mirrored = SimpleNamespace(
        MemberID="M002",
        SourceLayoutID="L002",
        StartNode=center_node,
        EndNode=mirror_outer_node,
        StartPoint=FakeVector(
            0.0,
            0.0,
            0.0,
        ),
        EndPoint=FakeVector(
            -500.0,
            0.0,
            0.0,
        ),
    )

    source_domain = domain_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    mirror_domain = domain_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            -500.0,
            0.0,
            0.0,
        ),
    )

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: (
            source_domain
            if obj is source
            else mirror_domain
        ),
    )

    layout = SimpleNamespace(
        StartPoint=FakeVector(
            0.0,
            0.0,
            0.0,
        ),
        EndPoint=FakeVector(
            500.0,
            0.0,
            0.0,
        ),
        touch=lambda: None,
    )

    monkeypatch.setattr(
        module,
        "layout_object_for_id",
        lambda doc, layout_id: layout,
    )

    updated_layouts = []

    monkeypatch.setattr(
        module,
        "update_layout_object_shape",
        lambda obj: updated_layouts.append(
            obj
        ),
    )

    removed = []

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda doc, obj: (
            removed.append(
                obj
            )
            or True
        ),
    )

    cleaned_nodes = []

    monkeypatch.setattr(
        module,
        "remove_node_if_unused",
        lambda doc, node: (
            cleaned_nodes.append(
                node
            )
            or True
        ),
    )

    result, merged = (
        module.merge_mirrored_member_pair_in_place(
            document,
            source,
            mirrored,
        )
    )

    assert merged
    assert result is source

    assert source.StartNode is mirror_outer_node

    assert (
        source.StartPoint.x,
        source.StartPoint.y,
        source.StartPoint.z,
    ) == (
        -500.0,
        0.0,
        0.0,
    )

    assert (
        layout.StartPoint.x,
        layout.StartPoint.y,
        layout.StartPoint.z,
    ) == (
        -500.0,
        0.0,
        0.0,
    )

    assert updated_layouts == [
        layout
    ]

    assert removed == [
        mirrored
    ]

    assert cleaned_nodes == [
        center_node
    ]


def test_angled_source_and_mirror_remain_separate(
    monkeypatch,
):
    document = FakeDocument()

    source = SimpleNamespace()
    mirrored = SimpleNamespace()

    source_domain = domain_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            500.0,
            0.0,
            200.0,
        ),
    )

    mirror_domain = domain_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            -500.0,
            0.0,
            200.0,
        ),
    )

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: (
            source_domain
            if obj is source
            else mirror_domain
        ),
    )

    result, merged = (
        module.merge_mirrored_member_pair_in_place(
            document,
            source,
            mirrored,
        )
    )

    assert not merged
    assert result is mirrored
    assert document.recompute_count == 0


def test_plane_batch_returns_source_object_for_continuous_pair(
    monkeypatch,
):
    source = SimpleNamespace(
        SourceLayoutID="L001"
    )

    temporary_mirror = SimpleNamespace(
        SourceLayoutID="L002"
    )

    monkeypatch.setattr(
        module,
        "source_treatment_snapshots",
        lambda document, objects: (),
    )

    monkeypatch.setattr(
        module,
        "mirror_member_object_across_plane",
        lambda document, obj, plane, offset=0.0: temporary_mirror,
    )

    monkeypatch.setattr(
        module,
        "merge_mirrored_member_pair_in_place",
        lambda document, source_object, mirrored_object: (
            source_object,
            True,
        ),
    )

    monkeypatch.setattr(
        module,
        "preserve_plane_mirrored_treatments",
        lambda *args, **kwargs: (),
    )

    result = (
        module.mirror_member_objects_across_plane(
            object(),
            [
                source,
            ],
            "YZ",
        )
    )

    assert result == (
        source,
    )


def test_layout_map_keeps_source_identity_after_continuous_merge():
    source = SimpleNamespace(
        SourceLayoutID="L001"
    )

    assert (
        module.mirrored_layout_id_map(
            [
                source,
            ],
            [
                source,
            ],
        )
        == {
            "L001": "L001",
        }
    )
