"""FreeCAD command for creating a ForgeCAD member between two nodes."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad import LayoutLine
from forgecad.fabrication import Member, Node
from forgecad.geometry import Point3D
from forgecad.adapters.freecad import FrameRenderer
from forgecad.adapters.freecad.commands.draw_layout_line import (
    create_layout_line_object,
    ensure_layout_id,
)
from forgecad.adapters.freecad.commands.generate_from_selection import (
    project_from_document,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


COMMAND_NAME = "ForgeCAD_CreateMemberBetweenNodes"


def is_forgecad_node(obj):
    """Return True when an object is a generated ForgeCAD node."""

    if obj is None:
        return False

    required_properties = (
        "NodeID",
        "Position",
    )

    return all(
        hasattr(
            obj,
            property_name,
        )
        for property_name
        in required_properties
    )


def selected_nodes():
    """Return exactly two selected ForgeCAD nodes."""

    selection = list(
        FreeCADGui.Selection.getSelection()
    )

    if len(selection) != 2:
        return []

    if not all(
        is_forgecad_node(obj)
        for obj in selection
    ):
        return []

    return selection


def node_from_object(obj):
    """Create a domain Node from a FreeCAD node object."""

    position = obj.Position

    return Node(
        x=float(
            position.x
        ),
        y=float(
            position.y
        ),
        z=float(
            position.z
        ),
    )


def next_member_id(frame_group):
    """Return the next available ForgeCAD member ID."""

    highest_number = 0

    for obj in frame_group.Group:
        member_id = str(
            getattr(
                obj,
                "MemberID",
                "",
            )
        ).strip()

        if not member_id.startswith(
            "M"
        ):
            continue

        try:
            number = int(
                member_id[1:]
            )

        except ValueError:
            continue

        highest_number = max(
            highest_number,
            number,
        )

    return (
        f"M{highest_number + 1:03d}"
    )


def create_member_between_nodes(
    document,
    start_node_object,
    end_node_object,
):
    """
    Create a persistent layout line and rendered tube
    between two ForgeCAD node objects.
    """

    start_node = node_from_object(
        start_node_object
    )

    end_node = node_from_object(
        end_node_object
    )

    if start_node == end_node:
        raise ValueError(
            "Cannot create a member between the same point."
        )

    # -----------------------------------------------------
    # Project configuration
    # -----------------------------------------------------

    project = project_from_document(
        document
    )

    profile = (
        project.tube_library.active_profile
    )

    material = (
        project.default_material
    )

    if material is None:
        raise ValueError(
            "ForgeCAD project has no default material."
        )

    # -----------------------------------------------------
    # Persistent layout geometry
    # -----------------------------------------------------

    layout_line = LayoutLine(
        start=Point3D(
            start_node.x,
            start_node.y,
            start_node.z,
        ),
        end=Point3D(
            end_node.x,
            end_node.y,
            end_node.z,
        ),
    )

    groups = initialize_project_tree(
        document
    )

    layout_object = (
        create_layout_line_object(
            document,
            layout_line,
        )
    )

    groups["Layout"].addObject(
        layout_object
    )

    source_layout_id = (
        ensure_layout_id(
            layout_object
        )
    )

    # -----------------------------------------------------
    # Domain member
    # -----------------------------------------------------

    member = Member(
        start=start_node,
        end=end_node,
        profile=profile,
        material=material,
    )

    # -----------------------------------------------------
    # FreeCAD tube
    # -----------------------------------------------------

    member_id = next_member_id(
        groups["Frame"]
    )

    renderer = FrameRenderer()

    rendered_object = (
        renderer.render_tube(
            document,
            member,
            member_id=member_id,
            source_layout_id=source_layout_id,
        )
    )

    groups["Frame"].addObject(
        rendered_object
    )

    document.recompute()

    return (
        layout_object,
        rendered_object,
    )


class CreateMemberBetweenNodesCommand:
    """Create one persistent tube between two selected ForgeCAD nodes."""

    def GetResources(self):
        return {
            "MenuText": "Create Member Between Nodes",
            "ToolTip": (
                "Create a persistent ForgeCAD tube "
                "between two selected nodes"
            ),
        }

    def Activated(self):
        document = (
            FreeCAD.ActiveDocument
        )

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Document",
                (
                    "Open or create a ForgeCAD "
                    "project first."
                ),
            )
            return

        selection = list(
            FreeCADGui.Selection.getSelection()
        )

        if len(selection) != 2:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select Two Nodes",
                (
                    "Select exactly two ForgeCAD nodes "
                    "before creating a member."
                ),
            )
            return

        if not all(
            is_forgecad_node(obj)
            for obj in selection
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                (
                    "Both selected objects must be "
                    "ForgeCAD nodes."
                ),
            )
            return

        try:
            layout_object, member_object = (
                create_member_between_nodes(
                    document,
                    selection[0],
                    selection[1],
                )
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

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.Selection.addSelection(
            member_object
        )

        FreeCADGui.activeDocument().activeView().fitAll()

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Create Member Between Nodes command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        CreateMemberBetweenNodesCommand(),
    )
    