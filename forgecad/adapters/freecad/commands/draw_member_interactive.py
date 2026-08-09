"""Interactive FreeCAD command for creating ForgeCAD tube members."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad import LayoutLine
from forgecad.adapters.freecad.commands.draw_layout_line import (
    create_layout_line_object,
    ensure_layout_id,
)
from forgecad.adapters.freecad.commands.draw_layout_line_interactive import (
    InteractiveLayoutLineTool,
)
from forgecad.adapters.freecad.commands.create_member_between_nodes import (
    create_member_between_nodes,
)
from forgecad.adapters.freecad.commands.generate_nodes import (
    create_node_object,
    point_key,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


COMMAND_NAME = "ForgeCAD_DrawMemberInteractive"

_active_tool = None


def existing_node_at_point(
    document,
    point,
):
    """Return an existing ForgeCAD node at the requested point."""

    groups = initialize_project_tree(
        document
    )

    target_key = point_key(
        point
    )

    for obj in groups["Nodes"].Group:
        if not hasattr(
            obj,
            "NodeID",
        ):
            continue

        if not hasattr(
            obj,
            "Position",
        ):
            continue

        if point_key(
            obj.Position
        ) == target_key:
            return obj

    return None


def next_node_id(
    nodes_group,
):
    """Return the next available ForgeCAD node ID."""

    highest_number = 0

    for obj in nodes_group.Group:
        node_id = str(
            getattr(
                obj,
                "NodeID",
                "",
            )
        ).strip()

        if not node_id.startswith(
            "N"
        ):
            continue

        try:
            number = int(
                node_id[1:]
            )
        except ValueError:
            continue

        highest_number = max(
            highest_number,
            number,
        )

    return (
        f"N{highest_number + 1:03d}"
    )


def get_or_create_node(
    document,
    point,
):
    """Return an existing node or create one at the point."""

    existing = existing_node_at_point(
        document,
        point,
    )

    if existing is not None:
        return existing

    groups = initialize_project_tree(
        document
    )

    nodes_group = groups[
        "Nodes"
    ]

    node_id = next_node_id(
        nodes_group
    )

    vector = FreeCAD.Vector(
        point.x,
        point.y,
        point.z,
    )

    node_object = create_node_object(
        document,
        vector,
        node_id,
    )

    nodes_group.addObject(
        node_object
    )

    document.recompute()

    return node_object


def remove_layout_object(
    document,
    layout_object,
):
    """
    Remove a temporary persistent layout object.

    create_member_between_nodes() creates its own persistent
    layout line, so the interactive tool does not need to
    keep a second copy.
    """

    if layout_object is None:
        return

    try:
        document.removeObject(
            layout_object.Name
        )
    except Exception:
        pass


class InteractiveMemberTool(
    InteractiveLayoutLineTool
):
    """Create persistent ForgeCAD tube members interactively."""

    def start(self):
        """Start interactive member creation."""

        super().start()

        self.show_status(
            "ForgeCAD Member: Click first point. "
            "Esc: Finish."
        )

    def commit_line(
        self,
        point,
    ):
        """
        Create/reuse endpoint nodes and create a persistent
        ForgeCAD member between them.
        """

        if self.start_point is None:
            return

        if self.start_point == point:
            return

        document = (
            FreeCAD.ActiveDocument
        )

        if document is None:
            self.stop()
            return

        try:
            start_node = get_or_create_node(
                document,
                self.start_point,
            )

            end_node = get_or_create_node(
                document,
                point,
            )

            create_member_between_nodes(
                document,
                start_node,
                end_node,
            )

        except (
            ValueError,
            KeyError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Member Creation Failed",
                str(error),
            )
            return

        # Continue drawing from the endpoint just like the
        # existing interactive layout-line command.
        self.start_point = point
        self.last_resolved_point = None

        self.remove_object(
            self.start_marker
        )

        self.start_marker = None

        self.create_start_marker(
            self.start_point
        )

        self.remove_object(
            self.preview_line
        )

        self.preview_line = None

        self.update_snap_marker(
            None
        )

        self.clear_length_input()

        self.show_status(
            "ForgeCAD Member: Continue drawing. "
            "Move cursor to choose direction. "
            "Enter exact length if needed. "
            "Esc: Finish."
        )

        document.recompute()


class DrawMemberInteractiveCommand:
    """Start interactive point-to-point member creation."""

    def GetResources(self):
        return {
            "MenuText":
                "Draw Member Interactively",
            "ToolTip": (
                "Create persistent ForgeCAD tube members "
                "point-to-point with snapping, angle "
                "inference, and exact length input"
            ),
        }

    def Activated(self):
        global _active_tool

        document = (
            FreeCAD.ActiveDocument
        )

        if document is None:
            document = FreeCAD.newDocument(
                "ForgeCAD_Frame"
            )

        if _active_tool is not None:
            _active_tool.stop()

        _active_tool = (
            InteractiveMemberTool()
        )

        _active_tool.start()

    def IsActive(self):
        return True


def register_command() -> None:
    """Register the interactive member command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        DrawMemberInteractiveCommand(),
    )
    