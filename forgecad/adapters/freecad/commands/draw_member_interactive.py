"""Interactive FreeCAD command for creating ForgeCAD tube members."""

import math

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.geometry import Point3D
from forgecad.adapters.freecad.commands.draw_layout_line_interactive import (
    InteractiveLayoutLineTool,
    SNAP_DISTANCE_PIXELS,
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


def node_point(
    node_object,
):
    """Return a Point3D for a ForgeCAD node object."""

    position = (
        node_object.Position
    )

    return Point3D(
        float(position.x),
        float(position.y),
        float(position.z),
    )


class InteractiveMemberTool(
    InteractiveLayoutLineTool
):
    """Create persistent ForgeCAD tube members interactively."""

    def __init__(self):
        super().__init__()

        self.snapped_node = None
        self.current_snap_type = None

    def start(self):
        """Start interactive member creation."""

        super().start()

        self.show_status(
            "ForgeCAD Member: Click first point. "
            "Existing nodes have snap priority. "
            "Esc: Finish."
        )

    def stop(self):
        """Stop member creation and clear node-snap state."""

        self.snapped_node = None
        self.current_snap_type = None

        super().stop()

    def forgecad_nodes(self):
        """Return existing generated ForgeCAD node objects."""

        document = (
            FreeCAD.ActiveDocument
        )

        if document is None:
            return []

        groups = initialize_project_tree(
            document
        )

        nodes = []

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

            nodes.append(
                obj
            )

        return nodes

    def find_node_snap(
        self,
        position,
    ):
        """Return the nearest ForgeCAD node inside snap tolerance."""

        if position is None:
            return None

        mouse_x = float(
            position[0]
        )

        mouse_y = float(
            position[1]
        )

        nearest_node = None
        nearest_distance = (
            SNAP_DISTANCE_PIXELS
        )

        for node in self.forgecad_nodes():
            try:
                point = node_point(
                    node
                )

                screen_x, screen_y = (
                    self.point_to_screen(
                        point
                    )
                )

            except Exception:
                continue

            distance = math.hypot(
                screen_x - mouse_x,
                screen_y - mouse_y,
            )

            if distance <= nearest_distance:
                nearest_distance = (
                    distance
                )

                nearest_node = (
                    node
                )

        return nearest_node

    def resolved_point(
        self,
        position,
    ):
        """
        Resolve node snap, layout endpoint snap,
        angle inference, or free position.
        """

        # -------------------------------------------------
        # Highest priority: actual ForgeCAD nodes
        # -------------------------------------------------

        node = self.find_node_snap(
            position
        )

        if node is not None:
            self.snapped_node = (
                node
            )

            self.current_snap_type = (
                "NODE"
            )

            return (
                node_point(
                    node
                ),
                "NODE",
                None,
            )

        self.snapped_node = None

        # -------------------------------------------------
        # Second priority: existing layout endpoint
        # -------------------------------------------------

        endpoint = (
            super().find_snap_point(
                position
            )
        )

        if endpoint is not None:
            self.current_snap_type = (
                "ENDPOINT"
            )

            return (
                endpoint,
                "ENDPOINT",
                None,
            )

        # -------------------------------------------------
        # Free viewport position
        # -------------------------------------------------

        free_point = (
            self.screen_to_point(
                position
            )
        )

        if free_point is None:
            self.current_snap_type = None

            return (
                None,
                None,
                None,
            )

        if self.start_point is None:
            self.current_snap_type = None

            return (
                free_point,
                None,
                None,
            )

        # -------------------------------------------------
        # Angle inference
        # -------------------------------------------------

        inferred_point, snapped_angle = (
            self.infer_angle(
                free_point
            )
        )

        if snapped_angle is not None:
            self.current_snap_type = (
                "ANGLE"
            )

            return (
                inferred_point,
                "ANGLE",
                snapped_angle,
            )

        self.current_snap_type = None

        return (
            free_point,
            None,
            None,
        )

    def inference_name(
        self,
        snap_type,
        snapped_angle,
    ):
        """Return readable member snap information."""

        if (
            snap_type == "NODE"
            and self.snapped_node is not None
        ):
            return (
                "NODE "
                f"{self.snapped_node.NodeID}"
            )

        return super().inference_name(
            snap_type,
            snapped_angle,
        )

    def update_snap_marker(
        self,
        point,
    ):
        """Show snap marker with node-aware labeling."""

        super().update_snap_marker(
            point
        )

        if self.snap_marker is None:
            return

        if (
            self.current_snap_type == "NODE"
            and self.snapped_node is not None
        ):
            self.snap_marker.Label = (
                "Node Snap "
                f"{self.snapped_node.NodeID}"
            )

        elif (
            self.current_snap_type
            == "ENDPOINT"
        ):
            self.snap_marker.Label = (
                "Endpoint Snap"
            )

    def on_mouse_move(
        self,
        event,
    ):
        """Update node snapping, preview, and measurements."""

        position = event.get(
            "Position"
        )

        if position is None:
            return

        point, snap_type, snapped_angle = (
            self.resolved_point(
                position
            )
        )

        if point is None:
            return

        self.last_resolved_point = (
            point
        )

        if snap_type in (
            "NODE",
            "ENDPOINT",
        ):
            self.update_snap_marker(
                point
            )

        else:
            self.update_snap_marker(
                None
            )

        if self.start_point is None:
            if (
                snap_type == "NODE"
                and self.snapped_node is not None
            ):
                self.show_status(
                    "ForgeCAD Member | "
                    f"NODE {self.snapped_node.NodeID} | "
                    "Click to start | Esc: Finish"
                )

            elif snap_type == "ENDPOINT":
                self.show_status(
                    "ForgeCAD Member | "
                    "ENDPOINT | "
                    "Click to start | Esc: Finish"
                )

            else:
                self.show_status(
                    "ForgeCAD Member: "
                    "Click first point. "
                    "Existing nodes have snap priority. "
                    "Esc: Finish."
                )

            return

        self.update_preview_line(
            self.start_point,
            point,
        )

        self.update_measurement_display(
            point,
            snap_type,
            snapped_angle,
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
            start_node = (
                get_or_create_node(
                    document,
                    self.start_point,
                )
            )

            end_node = (
                get_or_create_node(
                    document,
                    point,
                )
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

        # Continue from the newly committed endpoint.
        self.start_point = point
        self.last_resolved_point = None

        self.snapped_node = None
        self.current_snap_type = None

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
            "Existing nodes have snap priority. "
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
                "point-to-point with node snapping, "
                "angle inference, and exact length input"
            ),
        }

    def Activated(self):
        global _active_tool

        document = (
            FreeCAD.ActiveDocument
        )

        if document is None:
            document = (
                FreeCAD.newDocument(
                    "ForgeCAD_Frame"
                )
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
    