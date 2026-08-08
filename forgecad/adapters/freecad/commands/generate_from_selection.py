"""Generate or regenerate a tube frame from ForgeCAD layout lines."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad import ApplicationType, DisplayUnits
from forgecad.adapters.freecad import FrameRenderer
from forgecad.adapters.freecad.document_tree import (
    clear_group,
    initialize_project_tree,
)
from forgecad.services import (
    build_frame_from_layout,
    create_project,
)
from forgecad.services.layout_conversion import (
    layout_from_selected_objects,
)


COMMAND_NAME = "ForgeCAD_GenerateFromSelection"


def project_from_document(document):
    """
    Build a ForgeCAD domain project from the active FreeCAD document.

    If the document was created by drawing layout geometry directly and
    has not been configured through New ForgeCAD Project, ForgeCAD's
    standard defaults are stored on the document and used.
    """

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

    # ---------------------------------------------------------
    # Application
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Display units
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Active tube profile
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Default material
    # ---------------------------------------------------------

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
    """
    Return the layout objects to use for frame generation.

    Only objects that actually belong to the ForgeCAD Layout group
    are treated as selected layout geometry.

    If no layout objects are selected, the complete project Layout
    group is returned.
    """

    groups = initialize_project_tree(
        document
    )

    layout_group = groups["Layout"]

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


class GenerateFromSelectionCommand:
    """Generate or regenerate the project's tube frame."""

    def GetResources(self):
        return {
            "MenuText": "Generate / Regenerate Frame",
            "ToolTip": (
                "Generate the ForgeCAD frame from selected "
                "layout lines, or regenerate from the full "
                "project layout when no layout lines are selected"
            ),
        }

    def Activated(self):
        document = FreeCAD.ActiveDocument

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Document",
                "Create or draw a ForgeCAD layout first.",
            )
            return

        layout_objects = (
            selected_or_project_layout_lines(
                document
            )
        )

        layout = layout_from_selected_objects(
            layout_objects
        )

        if layout.line_count == 0:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Layout Lines",
                (
                    "Draw or define one or more ForgeCAD "
                    "layout lines before generating the frame."
                ),
            )
            return

        try:
            project = project_from_document(
                document
            )
        except (
            ValueError,
            KeyError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "ForgeCAD Project Error",
                str(error),
            )
            return

        frame = build_frame_from_layout(
            project,
            layout,
        )

        groups = initialize_project_tree(
            document
        )

        # Remove the previously generated frame before rebuilding.
        clear_group(
            document,
            groups["Frame"],
        )

        # Clear any stale selection that may refer to an object
        # removed during regeneration.
        FreeCADGui.Selection.clearSelection()

        renderer = FrameRenderer()

        rendered_objects = (
            renderer.render_frame(
                document,
                frame,
            )
        )

        for obj in rendered_objects:
            groups["Frame"].addObject(
                obj
            )

        document.recompute()

        FreeCADGui.activeDocument().activeView().viewAxonometric()
        FreeCADGui.activeDocument().activeView().fitAll()

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
    