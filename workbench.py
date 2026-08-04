"""ForgeCAD FreeCAD workbench definition."""

import FreeCADGui


class ForgeCADWorkbench(FreeCADGui.Workbench):
    """Fabrication-first tube-frame design workbench."""

    MenuText = "ForgeCAD"
    ToolTip = "Design tube frames and fabricated structures."
    Icon = ""

    def Initialize(self):
        from forgecad.adapters.freecad.commands.create_demo_frame import (
            COMMAND_NAME,
            register_command,
        )

        register_command()

        self.appendToolbar(
            "ForgeCAD",
            [COMMAND_NAME],
        )

        self.appendMenu(
            "ForgeCAD",
            [COMMAND_NAME],
        )

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"
    