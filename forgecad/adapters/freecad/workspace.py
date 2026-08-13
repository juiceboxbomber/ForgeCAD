"""FreeCAD workspace and grid helpers for ForgeCAD projects."""

import FreeCAD
import FreeCADGui
import Part

from forgecad import (
    ProjectType,
    project_module_for_type,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


WORKSPACE_OBJECT_NAME = "ForgeCADWorkspace"
AXES_OBJECT_NAME = "ForgeCADWorkspaceAxes"


def _line(
    x1,
    y1,
    x2,
    y2,
):
    """Return one XY-plane FreeCAD line at Z=0."""

    return Part.makeLine(
        FreeCAD.Vector(
            float(x1),
            float(y1),
            0.0,
        ),
        FreeCAD.Vector(
            float(x2),
            float(y2),
            0.0,
        ),
    )


def _grid_positions(
    minimum,
    maximum,
    spacing,
):
    """Return stable grid coordinates including both workspace edges."""

    minimum = float(
        minimum
    )
    maximum = float(
        maximum
    )
    spacing = float(
        spacing
    )

    if spacing <= 0:
        raise ValueError(
            "Grid spacing must be greater than zero."
        )

    positions = []

    index = 0
    value = minimum

    while value <= maximum + 1e-9:
        positions.append(
            round(
                value,
                9,
            )
        )

        index += 1
        value = (
            minimum
            + index * spacing
        )

    if (
        not positions
        or abs(
            positions[
                -1
            ]
            - maximum
        )
        > 1e-9
    ):
        positions.append(
            maximum
        )

    return tuple(
        positions
    )


def workspace_bounds(
    width_mm,
    height_mm,
):
    """Return centered XY workspace bounds."""

    half_width = (
        float(
            width_mm
        )
        / 2.0
    )

    half_height = (
        float(
            height_mm
        )
        / 2.0
    )

    return (
        -half_width,
        half_width,
        -half_height,
        half_height,
    )


def build_workspace_grid_shape(
    width_mm,
    height_mm,
    major_grid_mm,
):
    """Build one compound shape containing boundary and major-grid lines."""

    (
        minimum_x,
        maximum_x,
        minimum_y,
        maximum_y,
    ) = workspace_bounds(
        width_mm,
        height_mm,
    )

    edges = []

    # Workspace boundary.
    edges.extend(
        [
            _line(
                minimum_x,
                minimum_y,
                maximum_x,
                minimum_y,
            ),
            _line(
                maximum_x,
                minimum_y,
                maximum_x,
                maximum_y,
            ),
            _line(
                maximum_x,
                maximum_y,
                minimum_x,
                maximum_y,
            ),
            _line(
                minimum_x,
                maximum_y,
                minimum_x,
                minimum_y,
            ),
        ]
    )

    # Major grid.
    for x in _grid_positions(
        minimum_x,
        maximum_x,
        major_grid_mm,
    ):
        if abs(
            x
        ) <= 1e-9:
            continue

        edges.append(
            _line(
                x,
                minimum_y,
                x,
                maximum_y,
            )
        )

    for y in _grid_positions(
        minimum_y,
        maximum_y,
        major_grid_mm,
    ):
        if abs(
            y
        ) <= 1e-9:
            continue

        edges.append(
            _line(
                minimum_x,
                y,
                maximum_x,
                y,
            )
        )

    return Part.makeCompound(
        edges
    )


def build_workspace_axes_shape(
    width_mm,
    height_mm,
):
    """Build the centered X/Y origin-axis reference."""

    (
        minimum_x,
        maximum_x,
        minimum_y,
        maximum_y,
    ) = workspace_bounds(
        width_mm,
        height_mm,
    )

    return Part.makeCompound(
        [
            _line(
                minimum_x,
                0.0,
                maximum_x,
                0.0,
            ),
            _line(
                0.0,
                minimum_y,
                0.0,
                maximum_y,
            ),
        ]
    )


def _ensure_workspace_properties(
    obj,
):
    """Ensure persistent workspace metadata exists."""

    property_definitions = (
        (
            "App::PropertyString",
            "ProjectType",
        ),
        (
            "App::PropertyLength",
            "WorkspaceWidth",
        ),
        (
            "App::PropertyLength",
            "WorkspaceHeight",
        ),
        (
            "App::PropertyLength",
            "MajorGridSpacing",
        ),
        (
            "App::PropertyLength",
            "MinorGridSpacing",
        ),
    )

    for (
        property_type,
        property_name,
    ) in property_definitions:
        if hasattr(
            obj,
            property_name,
        ):
            continue

        obj.addProperty(
            property_type,
            property_name,
            "ForgeCAD Workspace",
        )

    for property_name in (
        "ProjectType",
        "WorkspaceWidth",
        "WorkspaceHeight",
        "MajorGridSpacing",
        "MinorGridSpacing",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj


def create_or_update_workspace(
    document,
    project_type,
):
    """
    Create the visible ForgeCAD workspace for a project type.

    The workspace consists of one boundary/major-grid compound plus
    one centered X/Y axis object. Both live in the Settings group so
    they remain separate from actual fabrication layout geometry.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    module = project_module_for_type(
        ProjectType(
            project_type
        )
    )

    workspace = (
        module.workspace
    )

    groups = initialize_project_tree(
        document
    )

    settings_group = groups[
        "Settings"
    ]

    grid_object = document.getObject(
        WORKSPACE_OBJECT_NAME
    )

    if grid_object is None:
        grid_object = document.addObject(
            "Part::Feature",
            WORKSPACE_OBJECT_NAME,
        )
        grid_object.Label = (
            "Workspace Grid"
        )

    grid_object.Shape = (
        build_workspace_grid_shape(
            workspace.width_mm,
            workspace.height_mm,
            workspace.major_grid_mm,
        )
    )

    _ensure_workspace_properties(
        grid_object
    )

    grid_object.ProjectType = (
        module.project_type.value
    )
    grid_object.WorkspaceWidth = (
        workspace.width_mm
    )
    grid_object.WorkspaceHeight = (
        workspace.height_mm
    )
    grid_object.MajorGridSpacing = (
        workspace.major_grid_mm
    )
    grid_object.MinorGridSpacing = (
        workspace.minor_grid_mm
    )

    axes_object = document.getObject(
        AXES_OBJECT_NAME
    )

    if axes_object is None:
        axes_object = document.addObject(
            "Part::Feature",
            AXES_OBJECT_NAME,
        )
        axes_object.Label = (
            "Workspace Origin Axes"
        )

    axes_object.Shape = (
        build_workspace_axes_shape(
            workspace.width_mm,
            workspace.height_mm,
        )
    )

    if grid_object not in settings_group.Group:
        settings_group.addObject(
            grid_object
        )

    if axes_object not in settings_group.Group:
        settings_group.addObject(
            axes_object
        )

    try:
        grid_object.ViewObject.LineWidth = 1.0
    except Exception:
        pass

    try:
        axes_object.ViewObject.LineWidth = 2.0
    except Exception:
        pass

    document.recompute()

    return (
        grid_object,
        axes_object,
    )


def configure_workspace_view():
    """Set a predictable top view and frame the visible workspace."""

    gui_document = (
        FreeCADGui.activeDocument()
    )

    if gui_document is None:
        return

    view = (
        gui_document.activeView()
    )

    try:
        view.viewTop()
    except Exception:
        pass

    try:
        view.fitAll()
    except Exception:
        pass


def initialize_project_workspace(
    document,
    project_type,
):
    """Create workspace reference geometry and frame it in the active view."""

    objects = create_or_update_workspace(
        document,
        project_type,
    )

    configure_workspace_view()

    return objects
