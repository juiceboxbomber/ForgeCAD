"""Tests for ForgeCAD physical member-end extension."""

import math
import sys
import types


class FakeVector:
    """Minimal FreeCAD Vector replacement."""

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
        return math.sqrt(
            self.x * self.x
            + self.y * self.y
            + self.z * self.z
        )


# ---------------------------------------------------------
# Stub FreeCAD modules BEFORE importing ForgeCAD adapters.
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.Vector = (
    FakeVector
)

fake_freecadgui = types.ModuleType(
    "FreeCADGui"
)

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = fake_freecadgui

sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad import (
    member_notch,
    notch_geometry,
)


# Patch the actual module globals as well, so this file is
# independent of pytest import order and other test stubs.
member_notch.FreeCAD = (
    fake_freecad
)

notch_geometry.FreeCAD = (
    fake_freecad
)


class FakeMemberObject:
    """Minimal generated ForgeCAD member."""

    def __init__(
        self,
        start,
        end,
    ):
        self.StartPoint = start
        self.EndPoint = end

    def addProperty(
        self,
        property_type,
        property_name,
        property_group,
    ):
        if property_name in (
            "StartExtension",
            "EndExtension",
            "NotchThroughDiameter",
        ):
            setattr(
                self,
                property_name,
                0.0,
            )

        elif property_name == (
            "NotchEnabled"
        ):
            setattr(
                self,
                property_name,
                False,
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


def assert_close(
    actual,
    expected,
    tolerance=1e-6,
):
    """Assert that two numeric values are approximately equal."""

    assert (
        abs(
            float(actual)
            - float(expected)
        )
        <= tolerance
    )


def test_design_length_is_unchanged():
    start = FakeVector(
        0,
        0,
        0,
    )

    end = FakeVector(
        100,
        0,
        0,
    )

    assert (
        notch_geometry.design_member_length(
            start,
            end,
        )
        == 100.0
    )


def test_end_extension_moves_only_physical_end():
    start = FakeVector(
        0,
        0,
        0,
    )

    end = FakeVector(
        100,
        0,
        0,
    )

    physical_start, physical_end = (
        notch_geometry.extended_member_endpoints(
            start,
            end,
            end_extension=25.0,
        )
    )

    assert (
        physical_start.x
        == 0.0
    )

    assert (
        physical_end.x
        == 125.0
    )


def test_start_extension_moves_opposite_direction():
    start = FakeVector(
        0,
        0,
        0,
    )

    end = FakeVector(
        100,
        0,
        0,
    )

    physical_start, physical_end = (
        notch_geometry.extended_member_endpoints(
            start,
            end,
            start_extension=25.0,
        )
    )

    assert (
        physical_start.x
        == -25.0
    )

    assert (
        physical_end.x
        == 100.0
    )


def test_both_ends_can_extend_independently():
    start = FakeVector(
        0,
        0,
        0,
    )

    end = FakeVector(
        100,
        0,
        0,
    )

    physical_start, physical_end = (
        notch_geometry.extended_member_endpoints(
            start,
            end,
            start_extension=10.0,
            end_extension=20.0,
        )
    )

    assert (
        physical_start.x
        == -10.0
    )

    assert (
        physical_end.x
        == 120.0
    )


def test_extension_works_on_diagonal_member():
    start = FakeVector(
        0,
        0,
        0,
    )

    end = FakeVector(
        100,
        100,
        0,
    )

    physical_start, physical_end = (
        notch_geometry.extended_member_endpoints(
            start,
            end,
            end_extension=(
                math.sqrt(
                    200.0
                )
            ),
        )
    )

    assert (
        physical_start.x
        == 0.0
    )

    assert (
        physical_start.y
        == 0.0
    )

    assert_close(
        physical_end.x,
        110.0,
    )

    assert_close(
        physical_end.y,
        110.0,
    )


def test_configure_start_extension():
    obj = FakeMemberObject(
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
    )

    member_notch.configure_start_extension(
        obj,
        15.0,
    )

    assert (
        float(
            obj.StartExtension
        )
        == 15.0
    )


def test_configure_end_extension():
    obj = FakeMemberObject(
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
    )

    member_notch.configure_end_extension(
        obj,
        22.5,
    )

    assert (
        float(
            obj.EndExtension
        )
        == 22.5
    )


def test_physical_member_endpoints_use_stored_extensions():
    obj = FakeMemberObject(
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
    )

    member_notch.configure_start_extension(
        obj,
        10.0,
    )

    member_notch.configure_end_extension(
        obj,
        20.0,
    )

    start, end = (
        member_notch.physical_member_endpoints(
            obj
        )
    )

    assert (
        start.x
        == -10.0
    )

    assert (
        end.x
        == 120.0
    )


def test_clear_extensions_resets_both_ends():
    obj = FakeMemberObject(
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
    )

    member_notch.configure_start_extension(
        obj,
        10.0,
    )

    member_notch.configure_end_extension(
        obj,
        20.0,
    )

    member_notch.clear_extensions(
        obj
    )

    assert (
        float(
            obj.StartExtension
        )
        == 0.0
    )

    assert (
        float(
            obj.EndExtension
        )
        == 0.0
    )
    