"""ForgeCAD FreeCAD workbench definition."""

import FreeCADGui


class ForgeCADWorkbench(
    FreeCADGui.Workbench
):
    """Fabrication-first tube-frame design workbench."""

    MenuText = "ForgeCAD"

    ToolTip = (
        "Design tube frames and fabricated structures."
    )

    Icon = ""

    def Initialize(
        self,
    ):
        from forgecad.adapters.freecad.commands.new_project import (
            COMMAND_NAME as NEW_PROJECT_COMMAND,
            register_command as register_new_project_command,
        )

        from forgecad.adapters.freecad.commands.draw_layout_line import (
            COMMAND_NAME as DRAW_LAYOUT_LINE_COMMAND,
            register_command as register_draw_layout_line_command,
        )

        from forgecad.adapters.freecad.commands.define_layout_lines import (
            COMMAND_NAME as DEFINE_LAYOUT_LINES_COMMAND,
            register_command as register_define_layout_lines_command,
        )

        from forgecad.adapters.freecad.commands.draw_layout_line_interactive import (
            COMMAND_NAME as DRAW_LAYOUT_LINE_INTERACTIVE_COMMAND,
            register_command as register_draw_layout_line_interactive_command,
        )

        from forgecad.adapters.freecad.commands.generate_nodes import (
            COMMAND_NAME as GENERATE_NODES_COMMAND,
            register_command as register_generate_nodes_command,
        )

        from forgecad.adapters.freecad.commands.create_offset_node import (
            COMMAND_NAME as CREATE_OFFSET_NODE_COMMAND,
            register_command as register_create_offset_node_command,
        )

        from forgecad.adapters.freecad.commands.create_node_from_geometry import (
            COMMAND_NAME as CREATE_NODE_FROM_GEOMETRY_COMMAND,
            register_command as register_create_node_from_geometry_command,
        )

        from forgecad.adapters.freecad.commands.draw_member_interactive import (
            COMMAND_NAME as DRAW_MEMBER_INTERACTIVE_COMMAND,
            register_command as register_draw_member_interactive_command,
        )

        from forgecad.adapters.freecad.commands.create_member_between_nodes import (
            COMMAND_NAME as CREATE_MEMBER_BETWEEN_NODES_COMMAND,
            register_command as register_create_member_between_nodes_command,
        )

        from forgecad.adapters.freecad.commands.generate_from_selection import (
            COMMAND_NAME as GENERATE_FROM_SELECTION_COMMAND,
            register_command as register_generate_from_selection_command,
        )

        from forgecad.adapters.freecad.commands.member_properties import (
            COMMAND_NAME as MEMBER_PROPERTIES_COMMAND,
            register_command as register_member_properties_command,
        )

        from forgecad.adapters.freecad.commands.select_members import (
            COMMAND_NAME as SELECT_MEMBERS_COMMAND,
            register_command as register_select_members_command,
        )

        from forgecad.adapters.freecad.commands.inspect_joint import (
            COMMAND_NAME as INSPECT_JOINT_COMMAND,
            register_command as register_inspect_joint_command,
        )

        from forgecad.adapters.freecad.commands.next_joint_needing_attention import (
            COMMAND_NAME as NEXT_JOINT_COMMAND,
            register_command as register_next_joint_command,
        )

        from forgecad.adapters.freecad.commands.joint_review_summary import (
            COMMAND_NAME as JOINT_REVIEW_SUMMARY_COMMAND,
            register_command as register_joint_review_summary_command,
        )

        from forgecad.adapters.freecad.commands.cut_list import (
            COMMAND_NAME as CUT_LIST_COMMAND,
            register_command as register_cut_list_command,
        )

        register_new_project_command()

        register_draw_layout_line_command()

        register_define_layout_lines_command()

        register_draw_layout_line_interactive_command()

        register_generate_nodes_command()

        register_create_offset_node_command()

        register_create_node_from_geometry_command()

        register_draw_member_interactive_command()

        register_create_member_between_nodes_command()

        register_generate_from_selection_command()

        register_member_properties_command()

        register_select_members_command()

        register_inspect_joint_command()

        register_next_joint_command()

        register_joint_review_summary_command()

        register_cut_list_command()

        commands = [
            NEW_PROJECT_COMMAND,
            DRAW_LAYOUT_LINE_COMMAND,
            DEFINE_LAYOUT_LINES_COMMAND,
            DRAW_LAYOUT_LINE_INTERACTIVE_COMMAND,
            GENERATE_NODES_COMMAND,
            CREATE_OFFSET_NODE_COMMAND,
            CREATE_NODE_FROM_GEOMETRY_COMMAND,
            DRAW_MEMBER_INTERACTIVE_COMMAND,
            CREATE_MEMBER_BETWEEN_NODES_COMMAND,
            GENERATE_FROM_SELECTION_COMMAND,
            MEMBER_PROPERTIES_COMMAND,
            SELECT_MEMBERS_COMMAND,
            INSPECT_JOINT_COMMAND,
            NEXT_JOINT_COMMAND,
            JOINT_REVIEW_SUMMARY_COMMAND,
            CUT_LIST_COMMAND,
        ]

        self.appendToolbar(
            "ForgeCAD",
            commands,
        )

        self.appendMenu(
            "ForgeCAD",
            commands,
        )

    def Activated(
        self,
    ):
        pass

    def Deactivated(
        self,
    ):
        pass

    def GetClassName(
        self,
    ):
        return "Gui::PythonWorkbench"
    