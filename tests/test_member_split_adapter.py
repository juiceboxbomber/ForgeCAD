"""Tests for the FreeCAD Split Member adapter."""

import sys
import types
from types import SimpleNamespace


sys.modules[
    "FreeCAD"
] = types.ModuleType(
    "FreeCAD"
)

sys.modules[
    "FreeCADGui"
] = types.ModuleType(
    "FreeCADGui"
)

sys.modules[
    "Part"
] = types.ModuleType(
    "Part"
)

fake_pyside = types.ModuleType(
    "PySide"
)

fake_pyside.QtGui = SimpleNamespace(
    QDialog=object,
    QMessageBox=SimpleNamespace(
        warning=lambda *args, **kwargs: None,
    ),
)

sys.modules[
    "PySide"
] = fake_pyside


from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.adapters.freecad import (
    member_split_adapter as module,
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
            0.0,
            0.0,
            0.0,
        ),
        end=Node(
            1000.0,
            0.0,
            0.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )


def install_fake_node_creator(
    monkeypatch,
    created_nodes,
):
    fake_draw_module = types.ModuleType(
        "forgecad.adapters.freecad.commands.draw_member_interactive"
    )

    def fake_get_or_create_node(
        document,
        point,
    ):
        node_object = SimpleNamespace(
            Position=point,
        )

        created_nodes.append(
            (
                point,
                node_object,
            )
        )

        return node_object

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


def test_split_member_object_creates_two_replacement_members(
    monkeypatch,
):
    document = FakeDocument()
    source = make_member()
    source_object = object()

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: source,
    )

    created_nodes = []

    install_fake_node_creator(
        monkeypatch,
        created_nodes,
    )

    create_calls = []

    def fake_create(
        document,
        start_node,
        end_node,
        profile=None,
        material=None,
        refresh=True,
    ):
        index = (
            len(
                create_calls
            )
            + 1
        )

        layout = (
            f"layout-{index}"
        )

        member = (
            f"member-{index}"
        )

        create_calls.append(
            (
                start_node,
                end_node,
                profile,
                material,
                refresh,
            )
        )

        return (
            layout,
            member,
        )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        fake_create,
    )

    removed = []

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda document, obj: (
            removed.append(
                obj
            )
            or True
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

    result = module.split_member_object(
        document,
        source_object,
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    assert len(
        create_calls
    ) == 2

    assert result[
        0
    ] == "layout-1"

    assert result[
        1
    ] == "member-1"

    assert result[
        2
    ] == "layout-2"

    assert result[
        3
    ] == "member-2"

    assert removed == [
        source_object
    ]

    assert create_calls[
        0
    ][
        4
    ] is False

    assert create_calls[
        1
    ][
        4
    ] is False


def test_split_reuses_one_shared_split_node_for_both_members(
    monkeypatch,
):
    document = FakeDocument()
    source = make_member()

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: source,
    )

    created_nodes = []

    install_fake_node_creator(
        monkeypatch,
        created_nodes,
    )

    create_calls = []

    def fake_create(
        document,
        start_node,
        end_node,
        profile=None,
        material=None,
        refresh=True,
    ):
        create_calls.append(
            (
                start_node,
                end_node,
                refresh,
            )
        )

        return (
            object(),
            object(),
        )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        fake_create,
    )

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda document, obj: True,
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

    result = module.split_member_object(
        document,
        object(),
        Node(
            250.0,
            0.0,
            0.0,
        ),
    )

    split_node = result[
        4
    ]

    assert create_calls[
        0
    ][
        1
    ] is split_node

    assert create_calls[
        1
    ][
        0
    ] is split_node

    assert create_calls[
        0
    ][
        2
    ] is False

    assert create_calls[
        1
    ][
        2
    ] is False


def test_split_preserves_source_profile_and_material(
    monkeypatch,
):
    document = FakeDocument()
    source = make_member()

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: source,
    )

    install_fake_node_creator(
        monkeypatch,
        [],
    )

    properties = []

    def fake_create(
        document,
        start_node,
        end_node,
        profile=None,
        material=None,
        refresh=True,
    ):
        properties.append(
            (
                profile,
                material,
                refresh,
            )
        )

        return (
            object(),
            object(),
        )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        fake_create,
    )

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda document, obj: True,
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

    module.split_member_object(
        document,
        object(),
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    assert properties == [
        (
            source.profile,
            source.material,
            False,
        ),
        (
            source.profile,
            source.material,
            False,
        ),
    ]


def test_split_refreshes_topology_and_fabrication_after_removal(
    monkeypatch,
):
    document = FakeDocument()
    source = make_member()

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: source,
    )

    install_fake_node_creator(
        monkeypatch,
        [],
    )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        lambda *args, **kwargs: (
            object(),
            object(),
        ),
    )

    events = []

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda document, obj: (
            events.append(
                "remove"
            )
            or True
        ),
    )

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

    module.split_member_object(
        document,
        object(),
        Node(
            500.0,
            0.0,
            0.0,
        ),
    )

    assert events == [
        "remove",
        "topology",
        "fabrication",
    ]


def test_invalid_split_point_prevents_any_document_changes(
    monkeypatch,
):
    document = FakeDocument()
    source = make_member()

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: source,
    )

    create_calls = []

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        lambda *args, **kwargs: create_calls.append(
            args
        ),
    )

    removed = []

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda *args, **kwargs: removed.append(
            args
        ),
    )

    try:
        module.split_member_object(
            document,
            object(),
            Node(
                500.0,
                50.0,
                0.0,
            ),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected invalid split point to fail."
        )

    assert create_calls == []
    assert removed == []
