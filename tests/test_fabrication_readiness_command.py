"""Tests for ForgeCAD Fabrication Readiness command."""

import sys
import types


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


from forgecad.adapters.freecad.commands.fabrication_readiness import (
    readiness_text,
    readiness_title,
)


class FakeResult:
    """Minimal document-validation result."""

    def __init__(
        self,
        is_ready,
        total_joints,
        ready_joints,
        not_ready_joints,
        invalid_joints,
        conflict_count=0,
    ):
        self.is_ready = (
            is_ready
        )

        self.total_joints = (
            total_joints
        )

        self.ready_joints = (
            ready_joints
        )

        self.not_ready_joints = (
            not_ready_joints
        )

        self.invalid_joints = (
            invalid_joints
        )

        self.conflict_count = (
            conflict_count
        )


def test_ready_title():
    result = FakeResult(
        True,
        4,
        4,
        0,
        0,
    )

    assert (
        readiness_title(
            result
        )
        == "Frame Ready"
    )


def test_not_ready_title():
    result = FakeResult(
        False,
        4,
        2,
        2,
        1,
    )

    assert (
        readiness_title(
            result
        )
        == "Frame Not Ready"
    )


def test_ready_text():
    result = FakeResult(
        True,
        4,
        4,
        0,
        0,
    )

    text = readiness_text(
        result
    )

    assert (
        "Frame Ready for Fabrication"
        in text
    )

    assert (
        "Ready Joints: 4"
        in text
    )


def test_not_ready_text():
    result = FakeResult(
        False,
        5,
        3,
        2,
        1,
    )

    text = readiness_text(
        result
    )

    assert (
        "Frame Not Ready for Fabrication"
        in text
    )

    assert (
        "Not Ready: 2"
        in text
    )

    assert (
        "Invalid: 1"
        in text
    )


def test_empty_frame_text():
    result = FakeResult(
        False,
        0,
        0,
        0,
        0,
    )

    text = readiness_text(
        result
    )

    assert (
        "No frame joints are available."
        in text
    )

def test_fabrication_conflict_is_reported():
    result = FakeResult(
        False,
        6,
        6,
        0,
        0,
        conflict_count=2,
    )

    text = readiness_text(
        result
    )

    assert (
        "Frame Not Ready for Fabrication"
        in text
    )

    assert (
        "Fabrication Conflicts: 2"
        in text
    )
    