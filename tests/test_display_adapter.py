"""Tests for ForgeCAD FreeCAD display settings adapter."""

import sys
import types


sys.modules[
    "FreeCAD"
] = types.ModuleType(
    "FreeCAD"
)
sys.modules[
    "FreeCADGui"
] = types.ModuleType(
    "FreeCADGui"
)
sys.modules[
    "Part"
] = types.ModuleType(
    "Part"
)


from forgecad.display_settings import (
    DisplaySettings,
)
from forgecad.adapters.freecad.display import (
    apply_display_settings,
    display_settings_from_object,
)


class FakeViewObject:
    def __init__(self):
        self.LineColor = None
        self.LineWidth = None


class FakeObject:
    def __init__(
        self,
        name,
    ):
        self.Name = name
        self.ViewObject = FakeViewObject()
        self._properties = set()

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        self._properties.add(
            property_name
        )
        setattr(
            self,
            property_name,
            None,
        )

    def setEditorMode(
        self,
        property_name,
        mode,
    ):
        pass


class FakeLayoutObject(
    FakeObject
):
    def __init__(
        self,
        name="ForgeCADLayoutLine001",
    ):
        super().__init__(
            name
        )
        self.LayoutID = "layout-1"
        self.StartPoint = object()
        self.EndPoint = object()


class FakeDocument:
    def __init__(self):
        self.workspace = FakeObject(
            "ForgeCADWorkspace"
        )
        self.axes = FakeObject(
            "ForgeCADWorkspaceAxes"
        )
        self.layout = FakeLayoutObject()
        self.Objects = [
            self.workspace,
            self.axes,
            self.layout,
        ]
        self.recompute_count = 0

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADWorkspace":
            return self.workspace

        if name == "ForgeCADWorkspaceAxes":
            return self.axes

        return None

    def recompute(self):
        self.recompute_count += 1


def test_display_settings_are_persisted_and_restored():
    document = FakeDocument()

    settings = DisplaySettings(
        grid_color=(0.1, 0.2, 0.3),
        grid_line_width=1.5,
        axis_color=(0.9, 0.1, 0.1),
        axis_line_width=2.5,
        layout_line_color=(0.0, 1.0, 1.0),
        layout_line_width=4.0,
    )

    apply_display_settings(
        document,
        settings,
    )

    restored = display_settings_from_object(
        document.workspace
    )

    assert restored == settings


def test_apply_display_settings_updates_existing_objects():
    document = FakeDocument()

    settings = DisplaySettings(
        grid_color=(0.2, 0.2, 0.2),
        grid_line_width=0.75,
        axis_color=(1.0, 0.0, 0.0),
        axis_line_width=3.0,
        layout_line_color=(1.0, 1.0, 0.0),
        layout_line_width=5.0,
    )

    apply_display_settings(
        document,
        settings,
    )

    assert (
        document.workspace.ViewObject.LineColor
        == settings.grid_color
    )
    assert (
        document.workspace.ViewObject.LineWidth
        == settings.grid_line_width
    )

    assert (
        document.axes.ViewObject.LineColor
        == settings.axis_color
    )
    assert (
        document.axes.ViewObject.LineWidth
        == settings.axis_line_width
    )

    assert (
        document.layout.ViewObject.LineColor
        == settings.layout_line_color
    )
    assert (
        document.layout.ViewObject.LineWidth
        == settings.layout_line_width
    )

    assert document.recompute_count == 1

def test_display_settings_accept_freecad_rgba_property_colors():
    document = FakeDocument()

    document.workspace.GridColor = (
        0.1,
        0.2,
        0.3,
        1.0,
    )
    document.workspace.GridLineWidth = 1.0

    document.workspace.AxisColor = (
        0.9,
        0.1,
        0.1,
        1.0,
    )
    document.workspace.AxisLineWidth = 2.0

    document.workspace.LayoutLineColor = (
        1.0,
        1.0,
        0.0,
        1.0,
    )
    document.workspace.LayoutLineWidth = 3.0

    restored = display_settings_from_object(
        document.workspace
    )

    assert restored.grid_color == (
        0.1,
        0.2,
        0.3,
    )
    assert restored.axis_color == (
        0.9,
        0.1,
        0.1,
    )
    assert restored.layout_line_color == (
        1.0,
        1.0,
        0.0,
    )

