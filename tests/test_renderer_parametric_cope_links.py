"""Tests that rendered cope slots retain target-member links."""

import sys
import types


class FakeVector:
    def __init__(
        self,
        x=0.0,
        y=0.0,
        z=0.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


fake_freecad = sys.modules.get(
    "FreeCAD"
)

if fake_freecad is None:
    fake_freecad = types.ModuleType(
        "FreeCAD"
    )

    sys.modules[
        "FreeCAD"
    ] = fake_freecad

fake_freecad.Vector = FakeVector


fake_part = sys.modules.get(
    "Part"
)

if fake_part is None:
    fake_part = types.ModuleType(
        "Part"
    )

    sys.modules[
        "Part"
    ] = fake_part


import forgecad.adapters.freecad.renderer as renderer


class FakeDomainNode:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class FakeDomainMember:
    def __init__(
        self,
        start,
        end,
    ):
        self.start = start
        self.end = end


class FakeRenderedMember:
    def __init__(
        self,
    ):
        self.StartCopeTargetMember = None
        self.EndCopeTargetMember = None
        self.StartCope2TargetMember = None
        self.EndCope2TargetMember = None


class FakeFrame:
    def __init__(
        self,
        members,
    ):
        self.members = list(
            members
        )


class FakeCopeSpecification:
    def __init__(
        self,
        coped_member,
        target_member,
        coped_end,
    ):
        self.coped_member = coped_member
        self.target_member = target_member
        self.coped_end = coped_end
        self.target_outside_diameter = 44.45


def test_primary_start_cope_retains_rendered_target_member():
    branch = FakeDomainMember(
        FakeDomainNode(
            0.0,
            0.0,
            0.0,
        ),
        FakeDomainNode(
            0.0,
            500.0,
            0.0,
        ),
    )

    through = FakeDomainMember(
        FakeDomainNode(
            -500.0,
            0.0,
            0.0,
        ),
        FakeDomainNode(
            500.0,
            0.0,
            0.0,
        ),
    )

    frame = FakeFrame(
        [
            branch,
            through,
        ]
    )

    rendered_branch = FakeRenderedMember()
    rendered_through = FakeRenderedMember()

    specification = FakeCopeSpecification(
        branch,
        through,
        renderer.BRANCH_END_START,
    )

    original_clear = renderer.clear_notch
    original_configure = renderer.configure_start_cope

    renderer.clear_notch = (
        lambda obj: None
    )

    renderer.configure_start_cope = (
        lambda obj,
        start,
        end,
        diameter: None
    )

    try:
        renderer.configure_cope_specifications(
            frame,
            [
                rendered_branch,
                rendered_through,
            ],
            [
                specification,
            ],
        )
    finally:
        renderer.clear_notch = original_clear
        renderer.configure_start_cope = original_configure

    assert (
        rendered_branch.StartCopeTargetMember
        is rendered_through
    )


def test_secondary_start_cope_retains_second_rendered_target_member():
    branch = FakeDomainMember(
        FakeDomainNode(
            0.0,
            0.0,
            0.0,
        ),
        FakeDomainNode(
            0.0,
            500.0,
            0.0,
        ),
    )

    through_a = FakeDomainMember(
        FakeDomainNode(
            -500.0,
            0.0,
            0.0,
        ),
        FakeDomainNode(
            500.0,
            0.0,
            0.0,
        ),
    )

    through_b = FakeDomainMember(
        FakeDomainNode(
            0.0,
            -500.0,
            0.0,
        ),
        FakeDomainNode(
            0.0,
            500.0,
            0.0,
        ),
    )

    frame = FakeFrame(
        [
            branch,
            through_a,
            through_b,
        ]
    )

    rendered_branch = FakeRenderedMember()
    rendered_a = FakeRenderedMember()
    rendered_b = FakeRenderedMember()

    specifications = [
        FakeCopeSpecification(
            branch,
            through_a,
            renderer.BRANCH_END_START,
        ),
        FakeCopeSpecification(
            branch,
            through_b,
            renderer.BRANCH_END_START,
        ),
    ]

    original_clear = renderer.clear_notch
    original_primary = renderer.configure_start_cope
    original_secondary = renderer.configure_start_cope_secondary

    renderer.clear_notch = (
        lambda obj: None
    )

    renderer.configure_start_cope = (
        lambda obj,
        start,
        end,
        diameter: None
    )

    renderer.configure_start_cope_secondary = (
        lambda obj,
        start,
        end,
        diameter: None
    )

    try:
        renderer.configure_cope_specifications(
            frame,
            [
                rendered_branch,
                rendered_a,
                rendered_b,
            ],
            specifications,
        )
    finally:
        renderer.clear_notch = original_clear
        renderer.configure_start_cope = original_primary
        renderer.configure_start_cope_secondary = original_secondary

    assert (
        rendered_branch.StartCopeTargetMember
        is rendered_a
    )

    assert (
        rendered_branch.StartCope2TargetMember
        is rendered_b
    )


def test_primary_end_cope_retains_rendered_target_member():
    branch = FakeDomainMember(
        FakeDomainNode(
            0.0,
            500.0,
            0.0,
        ),
        FakeDomainNode(
            0.0,
            0.0,
            0.0,
        ),
    )

    through = FakeDomainMember(
        FakeDomainNode(
            -500.0,
            0.0,
            0.0,
        ),
        FakeDomainNode(
            500.0,
            0.0,
            0.0,
        ),
    )

    frame = FakeFrame(
        [
            branch,
            through,
        ]
    )

    rendered_branch = FakeRenderedMember()
    rendered_through = FakeRenderedMember()

    specification = FakeCopeSpecification(
        branch,
        through,
        renderer.BRANCH_END_END,
    )

    original_clear = renderer.clear_notch
    original_configure = renderer.configure_end_cope

    renderer.clear_notch = (
        lambda obj: None
    )

    renderer.configure_end_cope = (
        lambda obj,
        start,
        end,
        diameter: None
    )

    try:
        renderer.configure_cope_specifications(
            frame,
            [
                rendered_branch,
                rendered_through,
            ],
            [
                specification,
            ],
        )
    finally:
        renderer.clear_notch = original_clear
        renderer.configure_end_cope = original_configure

    assert (
        rendered_branch.EndCopeTargetMember
        is rendered_through
    )
    