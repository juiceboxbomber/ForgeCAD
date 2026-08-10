"""Tests for ForgeCAD dual-end tube copes."""

import sys
import types

import pytest


class FakeVector:
    """Minimal FreeCAD-like vector."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    @property
    def Length(self):
        return (
            self.x * self.x
            + self.y * self.y
            + self.z * self.z
        ) ** 0.5


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.Vector = FakeVector

sys.modules[
    "FreeCAD"
] = fake_freecad
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


from forgecad.adapters.freecad import (
    renderer,
)


renderer.FreeCAD = fake_freecad


class FakeMember:
    """Minimal domain-member identity."""

    pass


class FakeFrame:
    """Minimal frame."""

    def __init__(
        self,
        members,
    ):
        self.members = list(
            members
        )


class FakeRenderedObject:
    """Minimal rendered member object."""

    pass


class FakeTargetMember:
    """Minimal target member containing start/end nodes."""

    def __init__(
        self,
    ):
        self.start = types.SimpleNamespace(
            x=0,
            y=0,
            z=0,
        )
        self.end = types.SimpleNamespace(
            x=100,
            y=0,
            z=0,
        )


class FakeCopeSpecification:
    """Minimal generalized cope specification."""

    def __init__(
        self,
        member,
        member_end,
    ):
        self.coped_member = member
        self.coped_end = member_end
        self.target_member = FakeTargetMember()
        self.target_outside_diameter = 44.45


def test_same_member_can_have_start_and_end_copes(
    monkeypatch,
):
    member = FakeMember()

    frame = FakeFrame(
        [
            member,
        ]
    )

    rendered = FakeRenderedObject()

    calls = []

    monkeypatch.setattr(
        renderer,
        "clear_notch",
        lambda obj: None,
    )

    monkeypatch.setattr(
        renderer,
        "configure_start_cope",
        lambda obj, start, end, diameter: calls.append(
            (
                "start",
                obj,
                diameter,
            )
        ),
    )

    monkeypatch.setattr(
        renderer,
        "configure_end_cope",
        lambda obj, start, end, diameter: calls.append(
            (
                "end",
                obj,
                diameter,
            )
        ),
    )

    specifications = (
        FakeCopeSpecification(
            member,
            renderer.BRANCH_END_START,
        ),
        FakeCopeSpecification(
            member,
            renderer.BRANCH_END_END,
        ),
    )

    renderer.configure_cope_specifications(
        frame,
        [
            rendered,
        ],
        specifications,
    )

    assert calls == [
        (
            "start",
            rendered,
            44.45,
        ),
        (
            "end",
            rendered,
            44.45,
        ),
    ]


def test_duplicate_start_cope_is_rejected(
    monkeypatch,
):
    member = FakeMember()

    frame = FakeFrame(
        [
            member,
        ]
    )

    rendered = FakeRenderedObject()

    monkeypatch.setattr(
        renderer,
        "clear_notch",
        lambda obj: None,
    )

    monkeypatch.setattr(
        renderer,
        "configure_start_cope",
        lambda obj, start, end, diameter: None,
    )

    specifications = (
        FakeCopeSpecification(
            member,
            renderer.BRANCH_END_START,
        ),
        FakeCopeSpecification(
            member,
            renderer.BRANCH_END_START,
        ),
    )

    with pytest.raises(
        ValueError,
        match="same member end",
    ):
        renderer.configure_cope_specifications(
            frame,
            [
                rendered,
            ],
            specifications,
        )


def test_duplicate_end_cope_is_rejected(
    monkeypatch,
):
    member = FakeMember()

    frame = FakeFrame(
        [
            member,
        ]
    )

    rendered = FakeRenderedObject()

    monkeypatch.setattr(
        renderer,
        "clear_notch",
        lambda obj: None,
    )

    monkeypatch.setattr(
        renderer,
        "configure_end_cope",
        lambda obj, start, end, diameter: None,
    )

    specifications = (
        FakeCopeSpecification(
            member,
            renderer.BRANCH_END_END,
        ),
        FakeCopeSpecification(
            member,
            renderer.BRANCH_END_END,
        ),
    )

    with pytest.raises(
        ValueError,
        match="same member end",
    ):
        renderer.configure_cope_specifications(
            frame,
            [
                rendered,
            ],
            specifications,
        )
