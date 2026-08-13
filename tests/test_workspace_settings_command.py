"""Tests for the Workspace Settings command helper."""

import sys
import types

from forgecad.workspace_settings import (
    WorkspaceSettings,
)


# ---------------------------------------------------------
# Stub FreeCAD / PySide before importing adapter modules.
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.ActiveDocument = None

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_pyside = types.ModuleType(
    "PySide"
)


class FakeQDialog:
    """Minimal Qt dialog base class for adapter imports."""

    Accepted = 1

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        pass


fake_qtgui = types.SimpleNamespace(
    QDialog=FakeQDialog,
)

fake_pyside.QtGui = fake_qtgui

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = fake_freecad_gui

sys.modules[
    "PySide"
] = fake_pyside


from forgecad.adapters.freecad.commands.workspace_settings import (
    settings_from_dialog,
)


class FakeDialog:
    settings = WorkspaceSettings(
        width_mm=5000.0,
        height_mm=2400.0,
        major_grid_mm=200.0,
        minor_grid_mm=50.0,
        grid_visible=False,
        snap_enabled=False,
    )


def test_settings_from_dialog_returns_workspace_settings():
    settings = settings_from_dialog(
        FakeDialog()
    )

    assert settings.width_mm == 5000.0
    assert settings.height_mm == 2400.0
    assert settings.major_grid_mm == 200.0
    assert settings.minor_grid_mm == 50.0
    assert settings.grid_visible is False
    assert settings.snap_enabled is False
