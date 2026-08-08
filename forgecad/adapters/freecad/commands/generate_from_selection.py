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
    """Rebuild the ForgeCAD project configuration from the document."""

    project_object = document.getObject("ForgeCADProject")

    if project_object is None:
        raise ValueError(
            "No ForgeCAD project was found in the active document. "
            "Create a ForgeCAD project first."
        )

    application_value = getattr(
        project_object,
        "Application",
        ApplicationType.GENERAL.value,
    )

    display_units_value = getattr(
        project_object,
        "DisplayUnits",
        DisplayUnits.MILLIMETERS.value,
    )

    active_profile_name = getattr(
        project_object,
        "ActiveTubeProfile",
        "",
    )

    if not active_profile_name:
        raise ValueError(
            "The ForgeCAD project does not have an active tube profile."
        )

    project = create_project(
        name=project_object.Label,
        application=ApplicationType(application_value),
        display_units=DisplayUnits(display_units_value),
        active_profile_name=active_profile_name,
    )

    return project


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
                "Create or open a ForgeCAD project first.",
            )
            return

        try:
            project = project_from_document(document)
        except (ValueError, KeyError) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "ForgeCAD Project Required",
                str(error),
            )
            return

        selected_objects = FreeCADGui.Selection.getSelection()

        layout = layout_from_selected_objects(
            selected_objects
        )

        if layout.line_count == 0:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Layout Lines Selected",
                "Select one or more ForgeCAD layout lines first.",
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

        rendered_objects = renderer.render_frame(
            document,
            frame,
        )

        for obj in rendered_objects:
            groups["Frame"].addObject(obj)

            obj.addProperty(
                "App::PropertyString",
                "TubeProfile",
                "ForgeCAD",
            )
            obj.TubeProfile = (
                project.active_profile_name or ""
            )

            obj.addProperty(
                "App::PropertyString",
                "Material",
                "ForgeCAD",
            )
            obj.Material = (
                project.default_material.name
                if project.default_material is not None
                else ""
            )

        document.recompute()

        FreeCADGui.activeDocument().activeView().viewAxonometric()
        FreeCADGui.activeDocument().activeView().fitAll()

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


def register_command():
    """Register the command with FreeCAD."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        GenerateFromSelectionCommand(),
    )
    