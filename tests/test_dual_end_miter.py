"""Tests for ForgeCAD dual-end member miters."""

import sys
import types


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

fake_freecad.Vector = (
    FakeVector
)

fake_part = types.ModuleType(
    "Part"
)

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
] = fake_part


from forgecad.adapters.freecad import (
    renderer,
)


renderer.FreeCAD = (
    fake_freecad
)


class FakeMemberObject:
    """Minimal rendered member object."""

    def __init__(
        self,
    ):
        self.StartMiterEnabled = False
        self.EndMiterEnabled = False

    def addProperty(
        self,
        property_type,
        property_name,
        property_group,
    ):
        if (
            property_type
            == "App::PropertyBool"
        ):
            setattr(
                self,
                property_name,
                False,
            )

        elif (
            property_type
            == "App::PropertyLength"
        ):
            setattr(
                self,
                property_name,
                0.0,
            )

        else:
            setattr(
                self,
                property_name,
                FakeVector(
                    0,
                    0,
                    0,
                ),
            )

    def setEditorMode(
        self,
        property_name,
        mode,
    ):
        pass


class FakeMember:
    """Minimal domain member identity."""

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


class FakeSpecification:
    """Minimal miter specification."""

    def __init__(
        self,
        member,
        member_end,
        plane_point,
        plane_normal,
        keep_point,
    ):
        self.member = member
        self.member_end = member_end
        self.plane_point = plane_point
        self.plane_normal = plane_normal
        self.keep_point = keep_point


def test_same_member_can_have_start_and_end_miters(
    monkeypatch,
):
    member = FakeMember()

    frame = FakeFrame(
        [
            member,
        ]
    )

    rendered = (
        FakeMemberObject()
    )

    calls = []

    monkeypatch.setattr(
        renderer,
        "clear_miter",
        lambda obj: None,
    )

    monkeypatch.setattr(
        renderer,
        "configure_start_miter",
        lambda obj, point, normal, keep: calls.append(
            (
                "start",
                obj,
            )
        ),
    )

    monkeypatch.setattr(
        renderer,
        "configure_end_miter",
        lambda obj, point, normal, keep: calls.append(
            (
                "end",
                obj,
            )
        ),
    )

    specifications = (
        FakeSpecification(
            member=member,
            member_end=(
                renderer.MITER_END_START
            ),
            plane_point=(
                0,
                0,
                0,
            ),
            plane_normal=(
                1,
                -1,
                0,
            ),
            keep_point=(
                100,
                0,
                0,
            ),
        ),
        FakeSpecification(
            member=member,
            member_end=(
                renderer.MITER_END_END
            ),
            plane_point=(
                100,
                0,
                0,
            ),
            plane_normal=(
                1,
                1,
                0,
            ),
            keep_point=(
                0,
                0,
                0,
            ),
        ),
    )

    renderer.configure_miter_specifications(
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
        ),
        (
            "end",
            rendered,
        ),
    ]


def test_duplicate_start_miter_is_rejected(
    monkeypatch,
):
    member = FakeMember()

    frame = FakeFrame(
        [
            member,
        ]
    )

    rendered = (
        FakeMemberObject()
    )

    monkeypatch.setattr(
        renderer,
        "clear_miter",
        lambda obj: None,
    )

    monkeypatch.setattr(
        renderer,
        "configure_start_miter",
        lambda obj, point, normal, keep: None,
    )

    first = FakeSpecification(
        member=member,
        member_end=(
            renderer.MITER_END_START
        ),
        plane_point=(
            0,
            0,
            0,
        ),
        plane_normal=(
            1,
            -1,
            0,
        ),
        keep_point=(
            100,
            0,
            0,
        ),
    )

    second = FakeSpecification(
        member=member,
        member_end=(
            renderer.MITER_END_START
        ),
        plane_point=(
            0,
            0,
            0,
        ),
        plane_normal=(
            -1,
            1,
            0,
        ),
        keep_point=(
            100,
            0,
            0,
        ),
    )

    try:
        renderer.configure_miter_specifications(
            frame,
            [
                rendered,
            ],
            (
                first,
                second,
            ),
        )

    except ValueError as error:
        assert (
            "same member end"
            in str(error)
        )

    else:
        raise AssertionError(
            "Expected duplicate start miter to fail."
        )


def test_duplicate_end_miter_is_rejected(
    monkeypatch,
):
    member = FakeMember()

    frame = FakeFrame(
        [
            member,
        ]
    )

    rendered = (
        FakeMemberObject()
    )

    monkeypatch.setattr(
        renderer,
        "clear_miter",
        lambda obj: None,
    )

    monkeypatch.setattr(
        renderer,
        "configure_end_miter",
        lambda obj, point, normal, keep: None,
    )

    first = FakeSpecification(
        member=member,
        member_end=(
            renderer.MITER_END_END
        ),
        plane_point=(
            100,
            0,
            0,
        ),
        plane_normal=(
            1,
            1,
            0,
        ),
        keep_point=(
            0,
            0,
            0,
        ),
    )

    second = FakeSpecification(
        member=member,
        member_end=(
            renderer.MITER_END_END
        ),
        plane_point=(
            100,
            0,
            0,
        ),
        plane_normal=(
            -1,
            -1,
            0,
        ),
        keep_point=(
            0,
            0,
            0,
        ),
    )

    try:
        renderer.configure_miter_specifications(
            frame,
            [
                rendered,
            ],
            (
                first,
                second,
            ),
        )

    except ValueError as error:
        assert (
            "same member end"
            in str(error)
        )

    else:
        raise AssertionError(
            "Expected duplicate end miter to fail."
        )
    