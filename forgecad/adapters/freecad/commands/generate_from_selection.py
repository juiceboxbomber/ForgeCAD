"""Generate or regenerate a tube frame from ForgeCAD layout lines."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad import (
    ApplicationType,
    DisplayUnits,
)
from forgecad.adapters.freecad import (
    FrameRenderer,
)
from forgecad.adapters.freecad.commands.draw_layout_line import (
    ensure_layout_id,
)
from forgecad.adapters.freecad.document_tree import (
    clear_group,
    initialize_project_tree,
)
from forgecad.adapters.freecad.member_object import (
    ensure_member_node_links,
)
from forgecad.services import (
    build_frame_from_layout,
    create_project,
    create_default_tube_library,
)
from forgecad.services.layout_conversion import (
    layout_from_selected_objects,
)
from forgecad.adapters.freecad.joint_status_objects import (
    rebuild_joint_status_objects,
)


COMMAND_NAME = "ForgeCAD_GenerateFromSelection"


def project_from_document(
    document,
):
    """Build a ForgeCAD domain project from the FreeCAD document."""

    project_object = document.getObject(
        "ForgeCADProject"
    )

    default_project = create_project(
        name="ForgeCAD Project",
    )

    if project_object is None:
        initialize_project_tree(
            document
        )

        project_object = document.getObject(
            "ForgeCADProject"
        )

    if project_object is None:
        raise ValueError(
            "ForgeCAD could not initialize the project."
        )

    application_value = getattr(
        project_object,
        "Application",
        "",
    )

    if not application_value:
        application_value = (
            default_project.application.value
        )

        if not hasattr(
            project_object,
            "Application",
        ):
            project_object.addProperty(
                "App::PropertyString",
                "Application",
                "ForgeCAD",
            )

        project_object.Application = (
            application_value
        )

    display_units_value = getattr(
        project_object,
        "DisplayUnits",
        "",
    )

    if not display_units_value:
        display_units_value = (
            default_project.display_units.value
        )

        if not hasattr(
            project_object,
            "DisplayUnits",
        ):
            project_object.addProperty(
                "App::PropertyString",
                "DisplayUnits",
                "ForgeCAD",
            )

        project_object.DisplayUnits = (
            display_units_value
        )

    active_profile_name = getattr(
        project_object,
        "ActiveTubeProfile",
        "",
    )

    if not active_profile_name:
        active_profile_name = (
            default_project.active_profile_name
        )

        if not active_profile_name:
            raise ValueError(
                "ForgeCAD's default project does not "
                "define an active tube profile."
            )

        if not hasattr(
            project_object,
            "ActiveTubeProfile",
        ):
            project_object.addProperty(
                "App::PropertyString",
                "ActiveTubeProfile",
                "ForgeCAD",
            )

        project_object.ActiveTubeProfile = (
            active_profile_name
        )

    default_material = (
        default_project.default_material
    )

    if default_material is not None:
        if not hasattr(
            project_object,
            "DefaultMaterial",
        ):
            project_object.addProperty(
                "App::PropertyString",
                "DefaultMaterial",
                "ForgeCAD",
            )

        if not project_object.DefaultMaterial:
            project_object.DefaultMaterial = (
                default_material.name
            )

    document.recompute()

    return create_project(
        name=project_object.Label,
        application=ApplicationType(
            application_value
        ),
        display_units=DisplayUnits(
            display_units_value
        ),
        active_profile_name=active_profile_name,
    )


def selected_or_project_layout_lines(
    document,
):
    """Return selected layout objects, or the full Layout group."""

    groups = initialize_project_tree(
        document
    )

    layout_group = groups[
        "Layout"
    ]

    layout_objects = list(
        layout_group.Group
    )

    selected_objects = list(
        FreeCADGui.Selection.getSelection()
    )

    selected_layout_objects = [
        obj
        for obj in selected_objects
        if obj in layout_objects
    ]

    if selected_layout_objects:
        return selected_layout_objects

    return layout_objects


def project_layout_lines(
    document,
):
    """
    Return every ForgeCAD layout object.

    This intentionally ignores the current GUI selection and is
    used when another command needs a complete frame regeneration.
    """

    groups = initialize_project_tree(
        document
    )

    return list(
        groups[
            "Layout"
        ].Group
    )


def layout_ids_for_objects(
    objects,
):
    """Return stable IDs for layout objects."""

    return [
        ensure_layout_id(
            obj
        )
        for obj in objects
    ]


def profile_overrides_for_objects(
    objects,
):
    """Return stored tube-profile overrides for layout objects."""

    overrides = []

    library = (
        create_default_tube_library()
    )

    valid_names = set(
        library.names
    )

    for obj in objects:
        override = getattr(
            obj,
            "TubeProfileOverride",
            "",
        )

        if override not in valid_names:
            override = ""

        overrides.append(
            override
        )

    return overrides


def apply_profile_overrides(
    rendered_objects,
    overrides,
):
    """Restore stored tube-profile overrides to generated members."""

    if (
        len(rendered_objects)
        != len(overrides)
    ):
        raise ValueError(
            "Profile override count does not match "
            "the number of generated members."
        )

    for obj, override in zip(
        rendered_objects,
        overrides,
    ):
        if not override:
            continue

        obj.TubeProfile = (
            override
        )


def _point_key(
    point,
    precision=6,
):
    """Return a stable coordinate key for a FreeCAD-like point."""

    return (
        round(
            float(point.x),
            precision,
        ),
        round(
            float(point.y),
            precision,
        ),
        round(
            float(point.z),
            precision,
        ),
    )


def _node_lookup(
    document,
):
    """Return ForgeCAD nodes indexed by their stored Position."""

    groups = initialize_project_tree(
        document
    )

    nodes = {}

    for obj in groups[
        "Nodes"
    ].Group:
        if (
            not hasattr(
                obj,
                "NodeID",
            )
            or not hasattr(
                obj,
                "Position",
            )
        ):
            continue

        nodes[
            _point_key(
                obj.Position
            )
        ] = obj

    return nodes


def restore_rendered_member_node_links(
    document,
    rendered_objects,
):
    """
    Restore persistent endpoint-node links on regenerated straight members.

    Bent tubes are intentionally ignored because their topology is represented
    by their solved curved centerline rather than StartPoint/EndPoint.
    """

    nodes = _node_lookup(
        document
    )

    for obj in rendered_objects:
        if (
            not hasattr(
                obj,
                "MemberID",
            )
            or not hasattr(
                obj,
                "StartPoint",
            )
            or not hasattr(
                obj,
                "EndPoint",
            )
        ):
            continue

        start_node = nodes.get(
            _point_key(
                obj.StartPoint
            )
        )

        end_node = nodes.get(
            _point_key(
                obj.EndPoint
            )
        )

        if (
            start_node is None
            and end_node is None
        ):
            continue

        ensure_member_node_links(
            obj,
            start_node,
            end_node,
        )


def document_object_names(
    document,
):
    """Return the internal names currently present in a document."""

    return {
        obj.Name
        for obj in getattr(
            document,
            "Objects",
            [],
        )
        if hasattr(
            obj,
            "Name",
        )
    }


def remove_objects_created_after(
    document,
    existing_names,
):
    """Remove objects created after a document snapshot."""

    existing_names = set(
        existing_names
    )

    created_objects = [
        obj
        for obj in list(
            getattr(
                document,
                "Objects",
                [],
            )
        )
        if (
            hasattr(
                obj,
                "Name",
            )
            and obj.Name
            not in existing_names
        )
    ]

    for obj in created_objects:
        try:
            document.removeObject(
                obj.Name
            )
        except Exception:
            pass

    try:
        document.recompute()
    except Exception:
        pass


def regenerate_frame(
    document,
    layout_objects=None,
    clear_selection=True,
    adjust_view=True,
):
    """
    Regenerate ForgeCAD frame geometry atomically.

    The existing Frame group remains untouched until a complete
    replacement frame has rendered successfully. If rendering fails,
    every object created by the failed attempt is removed and the
    previous frame remains intact.

    When layout_objects is omitted, the complete project layout
    is regenerated regardless of the current GUI selection.
    """

    if document is None:
        raise ValueError(
            "No active FreeCAD document."
        )

    if layout_objects is None:
        layout_objects = (
            project_layout_lines(
                document
            )
        )
    else:
        layout_objects = list(
            layout_objects
        )

    layout = (
        layout_from_selected_objects(
            layout_objects
        )
    )

    if layout.line_count == 0:
        raise ValueError(
            "Draw or define one or more ForgeCAD "
            "layout lines before generating the frame."
        )

    source_layout_ids = (
        layout_ids_for_objects(
            layout_objects
        )
    )

    profile_overrides = (
        profile_overrides_for_objects(
            layout_objects
        )
    )

    project = project_from_document(
        document
    )

    frame = build_frame_from_layout(
        project,
        layout,
    )

    groups = initialize_project_tree(
        document
    )

    existing_names = (
        document_object_names(
            document
        )
    )

    renderer = FrameRenderer()

    try:
        rendered_objects = (
            renderer.render_frame(
                document,
                frame,
                source_layout_ids=(
                    source_layout_ids
                ),
            )
        )

        apply_profile_overrides(
            rendered_objects,
            profile_overrides,
        )

        restore_rendered_member_node_links(
            document,
            rendered_objects,
        )

    except Exception:
        remove_objects_created_after(
            document,
            existing_names,
        )
        raise

    clear_group(
        document,
        groups[
            "Frame"
        ],
    )

    for obj in rendered_objects:
        groups[
            "Frame"
        ].addObject(
            obj
        )

    if clear_selection:
        FreeCADGui.Selection.clearSelection()

    document.recompute()

    rebuild_joint_status_objects(
        document
    )

    if adjust_view:
        gui_document = (
            FreeCADGui.activeDocument()
        )

        if gui_document is not None:
            view = (
                gui_document.activeView()
            )

            view.viewAxonometric()
            view.fitAll()

    return rendered_objects


class GenerateFromSelectionCommand:
    """Generate or regenerate the project's tube frame."""

    def GetResources(self):
        return {
            "MenuText":
                "Generate / Regenerate Frame",
            "ToolTip": (
                "Generate the frame from selected layout "
                "lines or the complete project layout"
            ),
        }

    def Activated(self):
        document = (
            FreeCAD.ActiveDocument
        )

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Document",
                (
                    "Create or draw a ForgeCAD "
                    "layout first."
                ),
            )
            return

        layout_objects = (
            selected_or_project_layout_lines(
                document
            )
        )

        try:
            regenerate_frame(
                document,
                layout_objects=(
                    layout_objects
                ),
                clear_selection=True,
                adjust_view=True,
            )

        except Exception as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Frame Generation Failed",
                str(error),
            )
            return

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command():
    """Register the command with FreeCAD."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        GenerateFromSelectionCommand(),
    )
