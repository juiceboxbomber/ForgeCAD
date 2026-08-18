"""Tests for non-selectable ForgeCAD workspace references."""

import sys
import types


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_part = types.ModuleType(
    "Part"
)

_original_modules = {
    name: sys.modules.get(
        name
    )
    for name in (
        "FreeCAD",
        "Part",
    )
}

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "Part"
] = fake_part


from forgecad.display_settings import (
    DisplaySettings,
)
from forgecad.adapters.freecad.display import (
    AXES_OBJECT_NAME,
    WORKSPACE_OBJECT_NAME,
    apply_display_settings,
    make_reference_object_nonselectable,
)


for _name, _module in _original_modules.items():
    if _module is None:
        sys.modules.pop(
            _name,
            None,
        )
    else:
        sys.modules[
            _name
        ] = _module


class FakeViewObject:
    def __init__(
        self,
    ):
        self.LineColor = None
        self.LineWidth = None
        self.Selectable = True


class FakeObject:
    def __init__(
        self,
        name,
    ):
        self.Name = name
        self.ViewObject = FakeViewObject()

    def setEditorMode(
        self,
        property_name,
        mode,
    ):
        pass

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        setattr(
            self,
            property_name,
            None,
        )


class FakeLayoutObject(
    FakeObject
):
    def __init__(
        self,
        name="ForgeCADLayoutLine",
    ):
        super().__init__(
            name
        )

        self.LayoutID = "layout-1"
        self.StartPoint = object()
        self.EndPoint = object()


class FakeDocument:
    def __init__(
        self,
    ):
        self.workspace = FakeObject(
            WORKSPACE_OBJECT_NAME
        )

        self.axes = FakeObject(
            AXES_OBJECT_NAME
        )

        self.layout = (
            FakeLayoutObject()
        )

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
        if (
            name
            == WORKSPACE_OBJECT_NAME
        ):
            return self.workspace

        if (
            name
            == AXES_OBJECT_NAME
        ):
            return self.axes

        return None

    def recompute(
        self,
    ):
        self.recompute_count += 1


def test_reference_object_is_made_nonselectable():
    obj = FakeObject(
        "Reference"
    )

    result = (
        make_reference_object_nonselectable(
            obj
        )
    )

    assert result is obj

    assert (
        obj.ViewObject.Selectable
        is False
    )


def test_display_settings_disable_reference_selection():
    document = FakeDocument()

    settings = (
        DisplaySettings()
    )

    apply_display_settings(
        document,
        settings,
        persist=False,
    )

    assert (
        document.workspace.ViewObject.Selectable
        is False
    )

    assert (
        document.axes.ViewObject.Selectable
        is False
    )


def test_layout_lines_remain_selectable():
    document = FakeDocument()

    settings = (
        DisplaySettings()
    )

    apply_display_settings(
        document,
        settings,
        persist=False,
    )

    assert (
        document.layout.ViewObject.Selectable
        is True
    )
