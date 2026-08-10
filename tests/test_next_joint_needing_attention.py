"""Tests for ForgeCAD joint-review navigation."""

import sys
import types


# ---------------------------------------------------------
# Preserve any modules that may already exist.
#
# This test must not leave fake FreeCAD/PySide modules behind
# because the rest of the ForgeCAD test suite may install its
# own more complete Qt and FreeCAD stubs.
# ---------------------------------------------------------

MODULE_NAMES = (
    "FreeCAD",
    "FreeCADGui",
    "Part",
    "PySide",
    "PySide.QtGui",
)

_previous_modules = {
    name: sys.modules.get(
        name
    )
    for name in MODULE_NAMES
}


# ---------------------------------------------------------
# Temporary FreeCAD / GUI stubs.
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecadgui = types.ModuleType(
    "FreeCADGui"
)

fake_part = types.ModuleType(
    "Part"
)

fake_pyside = types.ModuleType(
    "PySide"
)

fake_qtgui = types.ModuleType(
    "QtGui"
)

fake_pyside.QtGui = (
    fake_qtgui
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

sys.modules[
    "PySide"
] = fake_pyside

sys.modules[
    "PySide.QtGui"
] = fake_qtgui


# ---------------------------------------------------------
# Import only the module being tested while stubs are active.
# ---------------------------------------------------------

from forgecad.adapters.freecad.commands.next_joint_needing_attention import (
    attention_joint_objects,
    is_joint_status_object,
    joint_status_objects,
    next_attention_joint,
    selected_joint_status_object,
)


# ---------------------------------------------------------
# Restore sys.modules immediately.
#
# The imported ForgeCAD command retains references to the
# temporary modules it needed during import, while subsequent
# tests are free to install their own stubs.
# ---------------------------------------------------------

for module_name in MODULE_NAMES:
    previous = _previous_modules[
        module_name
    ]

    if previous is None:
        sys.modules.pop(
            module_name,
            None,
        )

    else:
        sys.modules[
            module_name
        ] = previous


class FakeVector:
    """Minimal FreeCAD-like vector."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


class FakeJoint:
    """Minimal Joints-tree object."""

    def __init__(
        self,
        joint_id,
        needs_attention,
    ):
        self.JointID = (
            joint_id
        )

        self.NodeKey = (
            joint_id
        )

        self.Position = FakeVector(
            0,
            0,
            0,
        )

        self.ReviewStatus = (
            "unreviewed"
            if needs_attention
            else "automatic"
        )

        self.NeedsAttention = (
            needs_attention
        )


class FakeGroup:
    """Minimal FreeCAD group."""

    def __init__(
        self,
        objects,
    ):
        self.Group = list(
            objects
        )


class FakeDocument:
    """Minimal FreeCAD document."""

    def __init__(
        self,
        joints=None,
        include_group=True,
    ):
        self.group = (
            FakeGroup(
                joints
                or []
            )
            if include_group
            else None
        )

    def getObject(
        self,
        name,
    ):
        if name == (
            "ForgeCADJoints"
        ):
            return (
                self.group
            )

        return None


def test_joint_status_object_is_recognized():
    joint = FakeJoint(
        "J001",
        True,
    )

    assert (
        is_joint_status_object(
            joint
        )
    )


def test_unrelated_object_is_not_joint_status():
    assert not (
        is_joint_status_object(
            object()
        )
    )


def test_joint_status_objects_preserve_group_order():
    first = FakeJoint(
        "J001",
        True,
    )

    second = FakeJoint(
        "J002",
        False,
    )

    document = FakeDocument(
        [
            first,
            second,
        ]
    )

    assert (
        joint_status_objects(
            document
        )
        == (
            first,
            second,
        )
    )


def test_attention_objects_are_filtered():
    first = FakeJoint(
        "J001",
        True,
    )

    second = FakeJoint(
        "J002",
        False,
    )

    third = FakeJoint(
        "J003",
        True,
    )

    document = FakeDocument(
        [
            first,
            second,
            third,
        ]
    )

    assert (
        attention_joint_objects(
            document
        )
        == (
            first,
            third,
        )
    )


def test_no_selection_returns_first_attention_joint():
    first = FakeJoint(
        "J001",
        False,
    )

    second = FakeJoint(
        "J002",
        True,
    )

    third = FakeJoint(
        "J003",
        True,
    )

    document = FakeDocument(
        [
            first,
            second,
            third,
        ]
    )

    assert (
        next_attention_joint(
            document
        )
        is second
    )


def test_navigation_continues_after_selected_joint():
    first = FakeJoint(
        "J001",
        True,
    )

    second = FakeJoint(
        "J002",
        False,
    )

    third = FakeJoint(
        "J003",
        True,
    )

    document = FakeDocument(
        [
            first,
            second,
            third,
        ]
    )

    assert (
        next_attention_joint(
            document,
            (
                first,
            ),
        )
        is third
    )


def test_navigation_wraps_to_beginning():
    first = FakeJoint(
        "J001",
        True,
    )

    second = FakeJoint(
        "J002",
        False,
    )

    third = FakeJoint(
        "J003",
        False,
    )

    document = FakeDocument(
        [
            first,
            second,
            third,
        ]
    )

    assert (
        next_attention_joint(
            document,
            (
                third,
            ),
        )
        is first
    )


def test_current_attention_joint_is_not_returned_when_another_exists():
    first = FakeJoint(
        "J001",
        True,
    )

    second = FakeJoint(
        "J002",
        True,
    )

    document = FakeDocument(
        [
            first,
            second,
        ]
    )

    assert (
        next_attention_joint(
            document,
            (
                first,
            ),
        )
        is second
    )


def test_single_attention_joint_wraps_back_to_itself():
    first = FakeJoint(
        "J001",
        True,
    )

    second = FakeJoint(
        "J002",
        False,
    )

    document = FakeDocument(
        [
            first,
            second,
        ]
    )

    assert (
        next_attention_joint(
            document,
            (
                first,
            ),
        )
        is first
    )


def test_all_reviewed_returns_none():
    first = FakeJoint(
        "J001",
        False,
    )

    second = FakeJoint(
        "J002",
        False,
    )

    document = FakeDocument(
        [
            first,
            second,
        ]
    )

    assert (
        next_attention_joint(
            document
        )
        is None
    )


def test_missing_joints_group_returns_none():
    document = FakeDocument(
        include_group=False
    )

    assert (
        joint_status_objects(
            document
        )
        == ()
    )

    assert (
        next_attention_joint(
            document
        )
        is None
    )


def test_selected_joint_status_requires_exactly_one():
    first = FakeJoint(
        "J001",
        True,
    )

    second = FakeJoint(
        "J002",
        True,
    )

    assert (
        selected_joint_status_object(
            (
                first,
            )
        )
        is first
    )

    assert (
        selected_joint_status_object(
            (
                first,
                second,
            )
        )
        is None
    )
    