"""FreeCAD command for creating a ForgeCAD project."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.dialogs import NewProjectDialog
from forgecad.services import create_project


COMMAND_NAME = "ForgeCAD_NewProject"


class NewProjectCommand:
    """Create a configured ForgeCAD project and FreeCAD document."""

    def GetResources(self):
        return {
            "MenuText": "New ForgeCAD Project",
            "ToolTip": "Create a new configured ForgeCAD project",
        }

    def Activated(self):
        dialog = NewProjectDialog(
            FreeCADGui.getMainWindow(),
        )

        if dialog.exec_() != QtGui.QDialog.Accepted:
            return

        project = create_project(
            name=dialog.project_name,
            application=dialog.application,
            display_units=dialog.display_units,
            active_profile_name=dialog.active_profile_name,
        )

        document_name = project.name.replace(" ", "_")
        document = FreeCAD.newDocument(document_name)

        root = document.addObject(
            "App::DocumentObjectGroupPython",
            "ForgeCADProject",
        )
        root.Label = project.name

        root.addProperty(
            "App::PropertyString",
            "Application",
            "ForgeCAD",
        )
        root.Application = project.application.value

        root.addProperty(
            "App::PropertyString",
            "DisplayUnits",
            "ForgeCAD",
        )
        root.DisplayUnits = project.display_units.value

        root.addProperty(
            "App::PropertyString",
            "ActiveTubeProfile",
            "ForgeCAD",
        )
        root.ActiveTubeProfile = project.active_profile_name or ""

        root.addProperty(
            "App::PropertyString",
            "DefaultMaterial",
            "ForgeCAD",
        )
        root.DefaultMaterial = (
            project.default_material.name
            if project.default_material is not None
            else ""
        )

        document.recompute()


def register_command() -> None:
    """Register the New Project command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        NewProjectCommand(),
    )
    