"""Tests for extending an existing bent tube through an adjacent joint."""

import sys
import types


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(
            x
        )
        self.y = float(
            y
        )
        self.z = float(
            z
        )


# ----------------------------------------------------------------------
# Minimal FreeCAD / Qt test environment
# ----------------------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.Vector = (
    FakeVector
)

fake_freecad.ActiveDocument = (
    None
)


fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_freecad_gui.Selection = (
    types.SimpleNamespace(
        getSelection=lambda: [],
        clearSelection=lambda: None,
        addSelection=lambda obj: None,
    )
)

fake_freecad_gui.getMainWindow = (
    lambda: None
)

fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)


fake_part = types.ModuleType(
    "Part"
)


class FakeQDialog:
    Accepted = 1


fake_pyside = types.ModuleType(
    "PySide"
)

fake_pyside.QtGui = (
    types.SimpleNamespace(
        QDialog=FakeQDialog,
    )
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


# ----------------------------------------------------------------------
# ForgeCAD imports
# ----------------------------------------------------------------------

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)

from forgecad.adapters.freecad.commands import (
    convert_joint_to_bend,
)


# ----------------------------------------------------------------------
# Domain fixtures
# ----------------------------------------------------------------------

def _material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def _profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def _tube():
    """
    Return an existing one-bend tube.

    This represents the result after converting the first
    joint in a three-segment continuous tube.
    """

    return BentTube(
        straight_runs=(
            StraightRun(
                900.0
            ),
            StraightRun(
                900.0
            ),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
                rotation_degrees=0.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


# ----------------------------------------------------------------------
# Fake FreeCAD structural objects
# ----------------------------------------------------------------------

class FakeBentProxy:
    """Minimal BentTubeProxy replacement."""

    def __init__(
        self,
        tube,
    ):
        self.tube = tube

    def _tube_from_properties(
        self,
        obj,
    ):
        return self.tube


class FakeBentObject:
    """Minimal FreeCAD bent-tube object."""

    def __init__(
        self,
        tube,
    ):
        self.Proxy = FakeBentProxy(
            tube
        )

        self.StartPoint = FakeVector(
            0.0,
            0.0,
            0.0,
        )

        self.InitialDirection = FakeVector(
            1.0,
            0.0,
            0.0,
        )

        self.InitialBendNormal = FakeVector(
            0.0,
            0.0,
            1.0,
        )

        self.TubeProfile = (
            "1.750 x .120 DOM"
        )

        self.BendCount = (
            tube.bend_count
        )


class FakeStraightObject:
    """Minimal generated straight-member object."""

    def __init__(
        self,
    ):
        self.MemberID = (
            "M003"
        )

        self.TubeProfile = (
            "1.750 x .120 DOM"
        )

        self.StartPoint = FakeVector(
            1000.0,
            1000.0,
            0.0,
        )

        self.EndPoint = FakeVector(
            2000.0,
            1000.0,
            0.0,
        )


# ----------------------------------------------------------------------
# Joint-type recognition
# ----------------------------------------------------------------------

def test_joint_with_bent_and_straight_member_is_extendable():
    """
    One bent tube plus one straight member represents the next
    convertible corner of a continuous fabricated tube.
    """

    bent = FakeBentObject(
        _tube()
    )

    straight = (
        FakeStraightObject()
    )

    assert (
        convert_joint_to_bend
        .is_extendable_bent_joint_objects(
            (
                bent,
                straight,
            )
        )
        is True
    )


def test_two_straight_members_are_not_extendable_bent_joint():
    """
    The existing two-straight-member conversion path remains separate.
    """

    first = (
        FakeStraightObject()
    )

    second = (
        FakeStraightObject()
    )

    assert (
        convert_joint_to_bend
        .is_extendable_bent_joint_objects(
            (
                first,
                second,
            )
        )
        is False
    )


def test_bent_plus_bent_is_not_supported_yet():
    """
    Joining two independently bent tubes is a different fabrication
    operation and must not accidentally use the extension path.
    """

    first = FakeBentObject(
        _tube()
    )

    second = FakeBentObject(
        _tube()
    )

    assert (
        convert_joint_to_bend
        .is_extendable_bent_joint_objects(
            (
                first,
                second,
            )
        )
        is False
    )


# ----------------------------------------------------------------------
# BentTube domain extension
# ----------------------------------------------------------------------

def test_appending_bend_definition_creates_second_bend():
    """
    Extending an existing bent tube adds one bend and one final run
    while preserving the existing tube definition.
    """

    original = (
        _tube()
    )

    result = (
        convert_joint_to_bend
        .append_bend_to_tube(
            original,
            final_run_length_mm=750.0,
            bend_angle_degrees=45.0,
            centerline_radius_mm=125.0,
            rotation_degrees=90.0,
        )
    )

    assert (
        result.bend_count
        == 2
    )

    assert tuple(
        run.length_mm
        for run
        in result.straight_runs
    ) == (
        900.0,
        900.0,
        750.0,
    )

    assert (
        result.bends[
            0
        ].angle_degrees
        == 90.0
    )

    assert (
        result.bends[
            0
        ].centerline_radius
        == 100.0
    )

    assert (
        result.bends[
            1
        ].angle_degrees
        == 45.0
    )

    assert (
        result.bends[
            1
        ].centerline_radius
        == 125.0
    )

    assert (
        result.bends[
            1
        ].rotation_degrees
        == 90.0
    )

    assert (
        result.profile
        == original.profile
    )

    assert (
        result.material
        == original.material
    )


def test_appending_bend_does_not_modify_original_tube():
    """
    BentTube is immutable domain data, so extension must produce a
    new definition rather than modifying the existing definition.
    """

    original = (
        _tube()
    )

    result = (
        convert_joint_to_bend
        .append_bend_to_tube(
            original,
            final_run_length_mm=750.0,
            bend_angle_degrees=45.0,
            centerline_radius_mm=125.0,
            rotation_degrees=90.0,
        )
    )

    assert (
        original.bend_count
        == 1
    )

    assert (
        result.bend_count
        == 2
    )

    assert tuple(
        run.length_mm
        for run
        in original.straight_runs
    ) == (
        900.0,
        900.0,
    )
    