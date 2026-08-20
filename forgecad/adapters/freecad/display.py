"""FreeCAD display-style helpers for ForgeCAD projects."""

from forgecad.display_settings import (
    DisplaySettings,
)


WORKSPACE_OBJECT_NAME = "ForgeCADWorkspace"
AXES_OBJECT_NAME = "ForgeCADWorkspaceAxes"
LAYOUT_OBJECT_PREFIX = "ForgeCADLayoutLine"


def _color_tuple(
    color,
):
    """Return an RGB tuple from a FreeCAD color value."""

    values = tuple(
        float(component)
        for component in color
    )

    if len(values) < 3:
        raise ValueError(
            "FreeCAD color must contain at least three components."
        )

    return (
        values[0],
        values[1],
        values[2],
    )


def ensure_display_properties(
    workspace_object,
):
    """Ensure persistent display settings exist on the workspace object."""

    if workspace_object is None:
        raise ValueError(
            "A ForgeCAD workspace object is required."
        )

    property_definitions = (
        ("App::PropertyColor", "GridColor"),
        ("App::PropertyFloat", "GridLineWidth"),
        ("App::PropertyColor", "AxisColor"),
        ("App::PropertyFloat", "AxisLineWidth"),
        ("App::PropertyColor", "LayoutLineColor"),
        ("App::PropertyFloat", "LayoutLineWidth"),
    )

    defaults = DisplaySettings()

    default_values = {
        "GridColor": defaults.grid_color,
        "GridLineWidth": defaults.grid_line_width,
        "AxisColor": defaults.axis_color,
        "AxisLineWidth": defaults.axis_line_width,
        "LayoutLineColor": defaults.layout_line_color,
        "LayoutLineWidth": defaults.layout_line_width,
    }

    for property_type, property_name in property_definitions:
        if not hasattr(
            workspace_object,
            property_name,
        ):
            workspace_object.addProperty(
                property_type,
                property_name,
                "ForgeCAD Display",
            )

            setattr(
                workspace_object,
                property_name,
                default_values[property_name],
            )

        try:
            workspace_object.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return workspace_object


def display_settings_from_object(
    workspace_object,
) -> DisplaySettings:
    """Read persistent display settings from a workspace object."""

    ensure_display_properties(
        workspace_object
    )

    return DisplaySettings(
        grid_color=_color_tuple(
            workspace_object.GridColor
        ),
        grid_line_width=float(
            workspace_object.GridLineWidth
        ),
        axis_color=_color_tuple(
            workspace_object.AxisColor
        ),
        axis_line_width=float(
            workspace_object.AxisLineWidth
        ),
        layout_line_color=_color_tuple(
            workspace_object.LayoutLineColor
        ),
        layout_line_width=float(
            workspace_object.LayoutLineWidth
        ),
    )


def display_settings_for_document(
    document,
) -> DisplaySettings:
    """Return persistent settings for a document or defaults."""

    if document is None:
        return DisplaySettings()

    workspace_object = document.getObject(
        WORKSPACE_OBJECT_NAME
    )

    if workspace_object is None:
        return DisplaySettings()

    return display_settings_from_object(
        workspace_object
    )


def persist_display_settings(
    workspace_object,
    settings,
):
    """Store validated display settings on the workspace object."""

    if not isinstance(
        settings,
        DisplaySettings,
    ):
        raise TypeError(
            "Display settings must be a DisplaySettings instance."
        )

    ensure_display_properties(
        workspace_object
    )

    workspace_object.GridColor = (
        settings.grid_color
    )
    workspace_object.GridLineWidth = (
        settings.grid_line_width
    )
    workspace_object.AxisColor = (
        settings.axis_color
    )
    workspace_object.AxisLineWidth = (
        settings.axis_line_width
    )
    workspace_object.LayoutLineColor = (
        settings.layout_line_color
    )
    workspace_object.LayoutLineWidth = (
        settings.layout_line_width
    )

    return workspace_object


def make_reference_object_nonselectable(
    obj,
):
    """Keep workspace reference geometry visible but non-selectable."""

    if obj is None:
        return None

    try:
        obj.ViewObject.Selectable = False
    except Exception:
        pass

    return obj


def apply_layout_line_style(
    layout_object,
    settings,
):
    """Apply layout-line appearance to one FreeCAD object."""

    if layout_object is None:
        return None

    layout_object.ViewObject.LineColor = (
        settings.layout_line_color
    )
    layout_object.ViewObject.LineWidth = (
        settings.layout_line_width
    )

    try:
        layout_object.ViewObject.Selectable = True
    except Exception:
        pass

    return layout_object


def layout_line_objects(
    document,
):
    """Return existing ForgeCAD layout-line objects."""

    if document is None:
        return []

    return [
        obj
        for obj in document.Objects
        if str(
            getattr(
                obj,
                "Name",
                "",
            )
        ).startswith(
            LAYOUT_OBJECT_PREFIX
        )
        or (
            hasattr(
                obj,
                "LayoutID",
            )
            and hasattr(
                obj,
                "StartPoint",
            )
            and hasattr(
                obj,
                "EndPoint",
            )
        )
    ]


def apply_display_settings(
    document,
    settings,
    persist=True,
):
    """Apply display settings to workspace references and layout lines."""

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if not isinstance(
        settings,
        DisplaySettings,
    ):
        raise TypeError(
            "Display settings must be a DisplaySettings instance."
        )

    workspace_object = document.getObject(
        WORKSPACE_OBJECT_NAME
    )

    if workspace_object is None:
        raise ValueError(
            "ForgeCAD workspace object was not found."
        )

    if persist:
        persist_display_settings(
            workspace_object,
            settings,
        )

    axes_object = document.getObject(
        AXES_OBJECT_NAME
    )

    workspace_object.ViewObject.LineColor = (
        settings.grid_color
    )
    workspace_object.ViewObject.LineWidth = (
        settings.grid_line_width
    )

    make_reference_object_nonselectable(
        workspace_object
    )

    if axes_object is not None:
        axes_object.ViewObject.LineColor = (
            settings.axis_color
        )
        axes_object.ViewObject.LineWidth = (
            settings.axis_line_width
        )

        make_reference_object_nonselectable(
            axes_object
        )

    for layout_object in layout_line_objects(
        document
    ):
        apply_layout_line_style(
            layout_object,
            settings,
        )

    document.recompute()

    return settings
