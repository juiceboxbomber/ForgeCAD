"""Tests for the FreeCAD Trim/Extend member adapter."""

import sys
import types
from types import SimpleNamespace

import pytest


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
    member_trim_extend_adapter as module,
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


def make_member(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=make_profile(),
        material=make_material(),
    )


def install_members(
    monkeypatch,
    source_object,
    source_member,
    target_object,
    target_member,
):
    def fake_reader(
        obj,
    ):
        if obj is source_object:
            return source_member

        if obj is target_object:
            return target_member

        raise AssertionError(
            "Unexpected member object."
        )

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        fake_reader,
    )


def install_node_creator(
    monkeypatch,
    calls,
):
    def fake_node_creator(
        document,
        point,
    ):
        obj = SimpleNamespace(
            Position=point,
        )

        calls.append(
            (
                point,
                obj,
            )
        )

        return obj

    monkeypatch.setattr(
        module,
        "_get_or_create_node",
        fake_node_creator,
    )


def install_refresh_spies(
    monkeypatch,
    events,
):
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


def test_extend_end_replaces_only_source_member(
    monkeypatch,
):
    document = FakeDocument()

    source_object = object()
    target_object = object()

    source = make_member(
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

    target = make_member(
        Node(
            1000.0,
            -500.0,
            0.0,
        ),
        Node(
            1000.0,
            500.0,
            0.0,
        ),
    )

    install_members(
        monkeypatch,
        source_object,
        source,
        target_object,
        target,
    )

    node_calls = []

    install_node_creator(
        monkeypatch,
        node_calls,
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
                profile,
                material,
                refresh,
            )
        )

        return (
            "layout",
            "replacement",
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

    events = []

    install_refresh_spies(
        monkeypatch,
        events,
    )

    result = (
        module.trim_extend_member_object(
            document,
            source_object,
            target_object,
        )
    )

    assert result[
        1
    ] == "replacement"

    assert result[
        2
    ] == Node(
        1000.0,
        0.0,
        0.0,
    )

    assert result[
        3
    ] == "end"

    assert result[
        4
    ] == "extend"

    assert removed == [
        source_object
    ]

    assert target_object not in removed

    assert create_calls[
        0
    ][
        4
    ] is False


def test_extend_before_start_moves_start_automatically(
    monkeypatch,
):
    document = FakeDocument()

    source_object = object()
    target_object = object()

    source = make_member(
        Node(
            500.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    target = make_member(
        Node(
            0.0,
            -500.0,
            0.0,
        ),
        Node(
            0.0,
            500.0,
            0.0,
        ),
    )

    install_members(
        monkeypatch,
        source_object,
        source,
        target_object,
        target,
    )

    install_node_creator(
        monkeypatch,
        [],
    )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        lambda *args, **kwargs: (
            "layout",
            "replacement",
        ),
    )

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda *args, **kwargs: True,
    )

    install_refresh_spies(
        monkeypatch,
        [],
    )

    result = (
        module.trim_extend_member_object(
            document,
            source_object,
            target_object,
        )
    )

    assert result[
        3
    ] == "start"

    assert result[
        4
    ] == "extend"


def test_trim_requires_explicit_endpoint_choice(
    monkeypatch,
):
    document = FakeDocument()

    source_object = object()
    target_object = object()

    source = make_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    target = make_member(
        Node(
            500.0,
            -500.0,
            0.0,
        ),
        Node(
            500.0,
            500.0,
            0.0,
        ),
    )

    install_members(
        monkeypatch,
        source_object,
        source,
        target_object,
        target,
    )

    with pytest.raises(
        ValueError,
        match="choosing",
    ):
        module.trim_extend_member_object(
            document,
            source_object,
            target_object,
        )


def test_trim_selected_end_is_replaced(
    monkeypatch,
):
    document = FakeDocument()

    source_object = object()
    target_object = object()

    source = make_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    target = make_member(
        Node(
            400.0,
            -500.0,
            0.0,
        ),
        Node(
            400.0,
            500.0,
            0.0,
        ),
    )

    install_members(
        monkeypatch,
        source_object,
        source,
        target_object,
        target,
    )

    node_calls = []

    install_node_creator(
        monkeypatch,
        node_calls,
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
                profile,
                material,
                refresh,
            )
        )

        return (
            "layout",
            "replacement",
        )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        fake_create,
    )

    monkeypatch.setattr(
        module,
        "remove_member_and_unused_layout",
        lambda *args, **kwargs: True,
    )

    install_refresh_spies(
        monkeypatch,
        [],
    )

    result = (
        module.trim_extend_member_object(
            document,
            source_object,
            target_object,
            endpoint="end",
        )
    )

    assert result[
        2
    ] == Node(
        400.0,
        0.0,
        0.0,
    )

    assert result[
        3
    ] == "end"

    assert result[
        4
    ] == "trim"

    assert node_calls[
        0
    ][
        0
    ] == source.start

    assert node_calls[
        1
    ][
        0
    ] == Node(
        400.0,
        0.0,
        0.0,
    )

    assert create_calls[
        0
    ][
        2
    ] is source.profile

    assert create_calls[
        0
    ][
        3
    ] is source.material

    assert create_calls[
        0
    ][
        4
    ] is False


def test_refresh_occurs_only_after_original_removal(
    monkeypatch,
):
    document = FakeDocument()

    source_object = object()
    target_object = object()

    source = make_member(
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

    target = make_member(
        Node(
            1000.0,
            -500.0,
            0.0,
        ),
        Node(
            1000.0,
            500.0,
            0.0,
        ),
    )

    install_members(
        monkeypatch,
        source_object,
        source,
        target_object,
        target,
    )

    install_node_creator(
        monkeypatch,
        [],
    )

    events = []

    def fake_create(
        *args,
        **kwargs,
    ):
        events.append(
            "create"
        )

        assert (
            kwargs[
                "refresh"
            ]
            is False
        )

        return (
            "layout",
            "replacement",
        )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        fake_create,
    )

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

    install_refresh_spies(
        monkeypatch,
        events,
    )

    module.trim_extend_member_object(
        document,
        source_object,
        target_object,
    )

    assert events == [
        "create",
        "remove",
        "topology",
        "fabrication",
    ]


def test_same_object_is_rejected_before_changes(
    monkeypatch,
):
    document = FakeDocument()
    obj = object()

    with pytest.raises(
        ValueError,
        match="different",
    ):
        module.trim_extend_member_object(
            document,
            obj,
            obj,
        )


def test_existing_endpoint_intersection_is_no_op_error(
    monkeypatch,
):
    document = FakeDocument()

    source_object = object()
    target_object = object()

    source = make_member(
        Node(
            0.0,
            0.0,
            0.0,
        ),
        Node(
            1000.0,
            0.0,
            0.0,
        ),
    )

    target = make_member(
        Node(
            1000.0,
            -500.0,
            0.0,
        ),
        Node(
            1000.0,
            500.0,
            0.0,
        ),
    )

    install_members(
        monkeypatch,
        source_object,
        source,
        target_object,
        target,
    )

    with pytest.raises(
        ValueError,
        match="endpoint",
    ):
        module.trim_extend_member_object(
            document,
            source_object,
            target_object,
        )
