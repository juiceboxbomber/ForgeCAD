"""Generate a tube frame from selected ForgeCAD layout lines."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad import ApplicationType, DisplayUnits
from forgecad.adapters.freecad import FrameRenderer
from forgecad.adapters.freecad.document_tree import (
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
    has not yet been configured through New ForgeCAD Project, use the
    standard ForgeCAD defaults and store those defaults on the document.
    """

    project_object = document.getObject("ForgeCADProject")

    # Build a default domain project first. This gives us ForgeCAD's
    # canonical default application, units, material, and tube profile.
    default_project = create_project(
        name="ForgeCAD Project",
    )

    if project_object is None:
        # The document has no project object at all.
        groups = initialize_project_tree(document)
        project_object = groups.get("Project")

        if project_object is None:
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
    # Default material metadata
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

    # Now create the actual domain project using the settings
    # stored on the FreeCAD project object.
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


class GenerateFromSelectionCommand:
    """Generate hollow tube members from selected layout lines."""

    def GetResources(self):
        return {
            "MenuText": "Generate Frame from Selection",
            "ToolTip": (
                "Convert selected ForgeCAD layout lines "
                "into hollow tube members using the active project"
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

        selected_objects = (
            FreeCADGui.Selection.getSelection()
        )

        layout = layout_from_selected_objects(
            selected_objects
        )

        if layout.line_count == 0:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Layout Lines Selected",
                (
                    "Select one or more ForgeCAD "
                    "layout lines first."
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
    