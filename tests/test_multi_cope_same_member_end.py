"""Regression tests for multiple copes on one member end."""

import sys
import types

fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "Part"
] = fake_part


from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.services.notch_analysis import (
    CopeSpecification,
)
from forgecad.adapters.freecad.renderer import (
    configure_cope_specifications,
)


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def make_material():
    return Material(
        name="DOM",
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


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


class FakeRenderedMember:
    pass


def test_same_member_end_accepts_second_cope(
    monkeypatch,
):
    center = Node(
        0,
        0,
        0,
    )

    branch = make_member(
        center,
        Node(
            0,
            500,
            0,
        ),
    )

    through = make_member(
        Node(
            -500,
            0,
            0,
        ),
        Node(
            500,
            0,
            0,
        ),
    )

    other_branch = make_member(
        center,
        Node(
            300,
            500,
            0,
        ),
    )

    rendered = FakeRenderedMember()

    first = CopeSpecification(
        joint=None,
        coped_member=branch,
        target_member=through,
        coped_end="start",
        angle_degrees=90.0,
        coped_outside_diameter=44.45,
        coped_inside_diameter=38.354,
        coped_wall_thickness=3.048,
        target_outside_diameter=44.45,
    )

    second = CopeSpecification(
        joint=None,
        coped_member=branch,
        target_member=other_branch,
        coped_end="start",
        angle_degrees=45.0,
        coped_outside_diameter=44.45,
        coped_inside_diameter=38.354,
        coped_wall_thickness=3.048,
        target_outside_diameter=44.45,
    )

    calls = []

    monkeypatch.setattr(
        "forgecad.adapters.freecad.renderer.clear_notch",
        lambda obj: None,
    )

    monkeypatch.setattr(
        (
            "forgecad.adapters.freecad.renderer."
            "target_axis_for_cope_specification"
        ),
        lambda specification: (
            FakeVector(
                0,
                0,
                0,
            ),
            FakeVector(
                100,
                0,
                0,
            ),
        ),
    )

    monkeypatch.setattr(
        (
            "forgecad.adapters.freecad.renderer."
            "configure_start_cope"
        ),
        lambda obj, start, end, diameter: calls.append(
            (
                "primary",
                obj,
                diameter,
            )
        ),
    )

    monkeypatch.setattr(
        (
            "forgecad.adapters.freecad.renderer."
            "configure_start_cope_secondary"
        ),
        lambda obj, start, end, diameter: calls.append(
            (
                "secondary",
                obj,
                diameter,
            )
        ),
    )

    fake_frame = type(
        "FakeFrame",
        (),
        {
            "members": [
                branch,
            ],
        },
    )()

    configure_cope_specifications(
        frame=fake_frame,
        rendered_objects=[
            rendered,
        ],
        specifications=[
            first,
            second,
        ],
    )

    assert calls == [
        (
            "primary",
            rendered,
            44.45,
        ),
        (
            "secondary",
            rendered,
            44.45,
        ),
    ]
