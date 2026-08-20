"""Tests for parametric cope target-member links."""

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


from forgecad.adapters.freecad.member_notch import (
    ensure_notch_properties,
    sync_cope_axes_from_target_members,
)


class FakeObject:
    def __init__(
        self,
    ):
        self.added_properties = []

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        self.added_properties.append(
            (
                property_type,
                property_name,
                group,
            )
        )

        setattr(
            self,
            property_name,
            None,
        )


class FakeTargetMember:
    def __init__(
        self,
        start,
        end,
    ):
        self.StartPoint = FakeVector(
            *start
        )

        self.EndPoint = FakeVector(
            *end
        )


def point_tuple(
    point,
):
    return (
        float(point.x),
        float(point.y),
        float(point.z),
    )


def test_notch_properties_include_parametric_cope_target_links():
    obj = FakeObject()

    ensure_notch_properties(
        obj
    )

    expected_links = (
        "StartCopeTargetMember",
        "EndCopeTargetMember",
        "StartCope2TargetMember",
        "EndCope2TargetMember",
    )

    for property_name in expected_links:
        assert hasattr(
            obj,
            property_name,
        )

        matching = [
            property_type
            for (
                property_type,
                added_name,
                group,
            )
            in obj.added_properties
            if added_name == property_name
        ]

        assert matching == [
            "App::PropertyLink"
        ]


def test_primary_start_cope_axis_follows_target_member():
    obj = FakeObject()

    ensure_notch_properties(
        obj
    )

    target = FakeTargetMember(
        start=(
            0.0,
            0.0,
            0.0,
        ),
        end=(
            1000.0,
            0.0,
            0.0,
        ),
    )

    obj.StartCopeEnabled = True
    obj.StartCopeTargetMember = target

    target.StartPoint = FakeVector(
        100.0,
        50.0,
        25.0,
    )

    target.EndPoint = FakeVector(
        1100.0,
        50.0,
        25.0,
    )

    changed = sync_cope_axes_from_target_members(
        obj
    )

    assert changed == 1

    assert point_tuple(
        obj.StartCopeThroughStart
    ) == (
        100.0,
        50.0,
        25.0,
    )

    assert point_tuple(
        obj.StartCopeThroughEnd
    ) == (
        1100.0,
        50.0,
        25.0,
    )


def test_primary_end_cope_axis_follows_target_member():
    obj = FakeObject()

    ensure_notch_properties(
        obj
    )

    target = FakeTargetMember(
        start=(
            0.0,
            0.0,
            0.0,
        ),
        end=(
            0.0,
            1000.0,
            0.0,
        ),
    )

    obj.EndCopeEnabled = True
    obj.EndCopeTargetMember = target

    changed = sync_cope_axes_from_target_members(
        obj
    )

    assert changed == 1

    assert point_tuple(
        obj.EndCopeThroughStart
    ) == (
        0.0,
        0.0,
        0.0,
    )

    assert point_tuple(
        obj.EndCopeThroughEnd
    ) == (
        0.0,
        1000.0,
        0.0,
    )


def test_secondary_cope_axes_follow_their_target_members():
    obj = FakeObject()

    ensure_notch_properties(
        obj
    )

    start_target = FakeTargetMember(
        start=(
            10.0,
            20.0,
            30.0,
        ),
        end=(
            110.0,
            120.0,
            130.0,
        ),
    )

    end_target = FakeTargetMember(
        start=(
            -10.0,
            -20.0,
            -30.0,
        ),
        end=(
            -110.0,
            -120.0,
            -130.0,
        ),
    )

    obj.StartCope2Enabled = True
    obj.StartCope2TargetMember = start_target

    obj.EndCope2Enabled = True
    obj.EndCope2TargetMember = end_target

    changed = sync_cope_axes_from_target_members(
        obj
    )

    assert changed == 2

    assert point_tuple(
        obj.StartCope2ThroughStart
    ) == (
        10.0,
        20.0,
        30.0,
    )

    assert point_tuple(
        obj.StartCope2ThroughEnd
    ) == (
        110.0,
        120.0,
        130.0,
    )

    assert point_tuple(
        obj.EndCope2ThroughStart
    ) == (
        -10.0,
        -20.0,
        -30.0,
    )

    assert point_tuple(
        obj.EndCope2ThroughEnd
    ) == (
        -110.0,
        -120.0,
        -130.0,
    )


def test_disabled_or_unlinked_cope_slots_are_not_changed():
    obj = FakeObject()

    ensure_notch_properties(
        obj
    )

    before = (
        point_tuple(
            obj.StartCopeThroughStart
        ),
        point_tuple(
            obj.StartCopeThroughEnd
        ),
    )

    changed = sync_cope_axes_from_target_members(
        obj
    )

    assert changed == 0

    assert (
        point_tuple(
            obj.StartCopeThroughStart
        ),
        point_tuple(
            obj.StartCopeThroughEnd
        ),
    ) == before
