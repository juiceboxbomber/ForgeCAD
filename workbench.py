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
        from forgecad.adapters.freecad.commands.generate_frame import (
            COMMAND_NAME as GENERATE_FRAME_COMMAND,
            register_command as register_generate_frame_command,
        )
        from forgecad.adapters.freecad.commands.draw_layout_line import (
            COMMAND_NAME as DRAW_LAYOUT_LINE_COMMAND,
            register_command as register_draw_layout_line_command,
        )
        from forgecad.adapters.freecad.commands.generate_from_selection import (
            COMMAND_NAME as GENERATE_FROM_SELECTION_COMMAND,
            register_command as register_generate_from_selection_command,
        )
        from forgecad.adapters.freecad.commands.define_layout_lines import (
           COMMAND_NAME as DEFINE_LAYOUT_LINES_COMMAND,
           register_command as register_define_layout_lines_command,
        )

        register_new_project_command()
        register_demo_command()
        register_generate_frame_command()
        register_draw_layout_line_command()
        register_define_layout_lines_command()
        register_generate_from_selection_command()
        
        commands = [
            NEW_PROJECT_COMMAND,
            DEMO_COMMAND,
            GENERATE_FRAME_COMMAND,
            DRAW_LAYOUT_LINE_COMMAND,
            GENERATE_FROM_SELECTION_COMMAND,
            DEFINE_LAYOUT_LINES_COMMAND,
        ]

        self.appendToolbar("ForgeCAD", commands)
        self.appendMenu("ForgeCAD", commands)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"