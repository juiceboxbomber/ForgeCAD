"""Tests for preserving joint treatments during Mirror Members."""

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
    Node,
)
from forgecad.adapters.freecad.commands import (
    mirror_members as module,
)


def vector(
    x,
    y,
    z=0.0,
):
    return SimpleNamespace(
        x=float(x),
        y=float(y),
        z=float(z),
    )


def member_object(
    source_layout_id,
    start,
    end,
):
    return SimpleNamespace(
        MemberID=source_layout_id.replace(
            "L",
            "M",
        ),
        SourceLayoutID=source_layout_id,
        StartPoint=start,
        EndPoint=end,
    )


def treatment(
    node_key,
    mode,
    through_layout_ids="",
):
    return SimpleNamespace(
        NodeKey=node_key,
        TreatmentMode=mode,
        ThroughLayoutIDs=through_layout_ids,
    )


def test_joint_point_belongs_to_two_selected_members():
    first = member_object(
        "L001",
        vector(0, 0),
        vector(500, 0),
    )

    second = member_object(
        "L002",
        vector(500, 0),
        vector(500, 500),
    )

    record = treatment(
        "500.000000,0.000000,0.000000",
        "both_mitered",
    )

    assert (
        module.treatment_belongs_to_selected_topology(
            record,
            [
                first,
                second,
            ],
        )
    )


def test_joint_with_only_one_selected_member_is_not_copied():
    first = member_object(
        "L001",
        vector(0, 0),
        vector(500, 0),
    )

    record = treatment(
        "500.000000,0.000000,0.000000",
        "both_mitered",
    )

    assert not (
        module.treatment_belongs_to_selected_topology(
            record,
            [
                first,
            ],
        )
    )


def test_layout_id_map_points_to_new_mirrored_members():
    sources = [
        member_object(
            "L001",
            vector(0, 0),
            vector(500, 0),
        ),
        member_object(
            "L002",
            vector(500, 0),
            vector(500, 500),
        ),
    ]

    mirrors = [
        SimpleNamespace(
            SourceLayoutID="L010"
        ),
        SimpleNamespace(
            SourceLayoutID="L011"
        ),
    ]

    assert (
        module.mirrored_layout_id_map(
            sources,
            mirrors,
        )
        == {
            "L001": "L010",
            "L002": "L011",
        }
    )


def test_miter_treatment_is_saved_at_mirrored_plane_node(
    monkeypatch,
):
    saved = []

    monkeypatch.setattr(
        module,
        "save_joint_treatment",
        lambda document, key, mode, ids=(): (
            saved.append(
                (
                    key,
                    mode,
                    ids,
                )
            )
            or object()
        ),
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

    module.save_mirrored_treatments(
        object(),
        (
            (
                "500.000000,250.000000,0.000000",
                "both_mitered",
                (),
            ),
        ),
        {},
        lambda key: (
            module.mirror_node_key_across_plane(
                key,
                "XZ",
            )
        ),
    )

    assert saved == [
        (
            "500.000000,-250.000000,0.000000",
            "both_mitered",
            (),
        )
    ]


def test_through_treatment_uses_new_mirrored_layout_id(
    monkeypatch,
):
    saved = []

    monkeypatch.setattr(
        module,
        "save_joint_treatment",
        lambda document, key, mode, ids=(): (
            saved.append(
                (
                    key,
                    mode,
                    ids,
                )
            )
            or object()
        ),
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

    module.save_mirrored_treatments(
        object(),
        (
            (
                "500.000000,250.000000,0.000000",
                "member_through",
                (
                    "L002",
                ),
            ),
        ),
        {
            "L002": "L011",
        },
        lambda key: key,
    )

    assert saved == [
        (
            "500.000000,250.000000,0.000000",
            "member_through",
            (
                "L011",
            ),
        )
    ]


def test_through_treatment_is_skipped_if_required_member_not_mirrored(
    monkeypatch,
):
    saved = []

    monkeypatch.setattr(
        module,
        "save_joint_treatment",
        lambda *args, **kwargs: saved.append(
            args
        ),
    )

    result = (
        module.save_mirrored_treatments(
            object(),
            (
                (
                    "500.000000,250.000000,0.000000",
                    "member_through",
                    (
                        "L099",
                    ),
                ),
            ),
            {},
            lambda key: key,
        )
    )

    assert result == ()
    assert saved == []


def test_centerline_treatment_key_uses_same_reflection_as_members(
    monkeypatch,
):
    saved = []

    monkeypatch.setattr(
        module,
        "save_joint_treatment",
        lambda document, key, mode, ids=(): (
            saved.append(
                key
            )
            or object()
        ),
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

    module.preserve_centerline_mirrored_treatments(
        object(),
        [
            SimpleNamespace(
                SourceLayoutID="L001"
            ),
        ],
        [
            SimpleNamespace(
                SourceLayoutID="L010"
            ),
        ],
        (
            (
                "300.000000,200.000000,0.000000",
                "both_mitered",
                (),
            ),
        ),
        Node(
            100.0,
            -1000.0,
            0.0,
        ),
        Node(
            100.0,
            1000.0,
            0.0,
        ),
    )

    assert saved == [
        "-100.000000,200.000000,0.000000"
    ]
