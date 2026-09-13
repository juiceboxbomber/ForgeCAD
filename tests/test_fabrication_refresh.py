"""Tests for incremental ForgeCAD fabrication refresh."""

import importlib
import sys
import types


sys.modules[
    "FreeCAD"
] = types.ModuleType(
    "FreeCAD"
)

sys.modules[
    "Part"
] = types.ModuleType(
    "Part"
)


module = importlib.import_module(
    "forgecad.adapters.freecad.fabrication_refresh"
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


class FakeMemberObject:
    def __init__(
        self,
        source_layout_id,
    ):
        self.SourceLayoutID = source_layout_id
        self.Proxy = types.SimpleNamespace(
            update_shape=self._update_shape
        )
        self.update_count = 0
        self.touch_count = 0

    def _update_shape(
        self,
        obj,
    ):
        assert obj is self
        self.update_count += 1

    def touch(
        self,
    ):
        self.touch_count += 1


class FakeFrame:
    def __init__(
        self,
        members,
    ):
        self.members = list(
            members
        )


def install_module(
    name,
    **attributes,
):
    original = sys.modules.get(
        name
    )

    fake = types.ModuleType(
        name
    )

    for key, value in attributes.items():
        setattr(
            fake,
            key,
            value,
        )

    sys.modules[
        name
    ] = fake

    return original


def restore_module(
    name,
    original,
):
    if original is None:
        sys.modules.pop(
            name,
            None,
        )
    else:
        sys.modules[
            name
        ] = original


def test_none_document_returns_false():
    assert (
        module.refresh_fabrication_for_document(
            None
        )
        is False
    )


def test_empty_document_returns_false():
    document = FakeDocument()

    originals = {}

    originals[
        "forgecad.adapters.freecad.joint_inspector_adapter"
    ] = install_module(
        "forgecad.adapters.freecad.joint_inspector_adapter",
        frame_member_objects=(
            lambda current_document: ()
        ),
        structural_member_from_freecad_object=(
            lambda obj: obj
        ),
    )

    originals[
        "forgecad.fabrication"
    ] = install_module(
        "forgecad.fabrication",
        Frame=FakeFrame,
    )

    originals[
        "forgecad.adapters.freecad.renderer"
    ] = install_module(
        "forgecad.adapters.freecad.renderer",
        configure_saved_fabrication=(
            lambda *args, **kwargs: None
        ),
    )

    try:
        result = (
            module.refresh_fabrication_for_document(
                document
            )
        )
    finally:
        for name, original in originals.items():
            restore_module(
                name,
                original,
            )

    assert result is False
    assert document.recompute_count == 0


def test_refresh_reuses_existing_member_objects_and_reapplies_fabrication():
    document = FakeDocument()

    first = FakeMemberObject(
        "L001"
    )
    second = FakeMemberObject(
        "L002"
    )

    domain_first = object()
    domain_second = object()

    calls = []

    originals = {}

    originals[
        "forgecad.adapters.freecad.joint_inspector_adapter"
    ] = install_module(
        "forgecad.adapters.freecad.joint_inspector_adapter",
        frame_member_objects=(
            lambda current_document: (
                first,
                second,
            )
        ),
        structural_member_from_freecad_object=(
            lambda obj: (
                domain_first
                if obj is first
                else domain_second
            )
        ),
    )

    originals[
        "forgecad.fabrication"
    ] = install_module(
        "forgecad.fabrication",
        Frame=FakeFrame,
    )

    def configure(
        current_document,
        frame,
        rendered_objects,
        source_layout_ids=None,
    ):
        calls.append(
            (
                current_document,
                tuple(
                    frame.members
                ),
                tuple(
                    rendered_objects
                ),
                tuple(
                    source_layout_ids
                ),
            )
        )

    originals[
        "forgecad.adapters.freecad.renderer"
    ] = install_module(
        "forgecad.adapters.freecad.renderer",
        configure_saved_fabrication=configure,
    )

    try:
        result = (
            module.refresh_fabrication_for_document(
                document
            )
        )
    finally:
        for name, original in originals.items():
            restore_module(
                name,
                original,
            )

    assert result is True

    assert calls == [
        (
            document,
            (
                domain_first,
                domain_second,
            ),
            (
                first,
                second,
            ),
            (
                "L001",
                "L002",
            ),
        )
    ]

    assert first.update_count == 1
    assert second.update_count == 1
    assert first.touch_count == 1
    assert second.touch_count == 1
    assert document.recompute_count == 1
