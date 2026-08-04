"""ForgeCAD FreeCAD workbench definition."""

import FreeCADGui


class ForgeCADWorkbench(FreeCADGui.Workbench):
    """Fabrication-first tube-frame design workbench."""

    MenuText = "ForgeCAD"
    ToolTip = "Design tube frames and fabricated structures."
    Icon = ""

    def Initialize(self):
        from forgecad.adapters.freecad.commands.create_demo_frame import (
            COMMAND_NAME as DEMO_COMMAND,
            register_command as register_demo_command,
        )
        from forgecad.adapters.freecad.commands.new_project import (
            COMMAND_NAME as NEW_PROJECT_COMMAND,
            register_command as register_new_project_command,
        )
        register_new_project_command()
        register_demo_command()

        commands = [
            NEW_PROJECT_COMMAND,
            DEMO_COMMAND,
        ]

        self.appendToolbar("ForgeCAD", commands)
        self.appendMenu("ForgeCAD", commands)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    