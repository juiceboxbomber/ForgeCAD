"""Tests for the Display Settings command helper."""

import sys
import types

from forgecad.display_settings import (
    DisplaySettings,
)


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)


class FakeQDialog:
    Accepted = 1

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        pass


class FakeQPushButton:
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        pass


fake_pyside = types.ModuleType(
    "PySide"
)
fake_pyside.QtGui = types.SimpleNamespace(
    QDialog=FakeQDialog,
    QPushButton=FakeQPushButton,
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "FreeCADGui"
] = fake_freecad_gui
sys.modules[
    "PySide"
] = fake_pyside


from forgecad.adapters.freecad.commands.display_settings import (
    settings_from_dialog,
)


class FakeDialog:
    settings = DisplaySettings(
        grid_color=(0.2, 0.2, 0.2),
        grid_line_width=0.5,
        axis_color=(1.0, 0.0, 0.0),
        axis_line_width=3.0,
        layout_line_color=(0.0, 1.0, 1.0),
        layout_line_width=5.0,
    )


def test_settings_from_dialog_returns_display_settings():
    settings = settings_from_dialog(
        FakeDialog()
    )

    assert settings.layout_line_color == (
        0.0,
        1.0,
        1.0,
    )
    assert settings.layout_line_width == 5.0
