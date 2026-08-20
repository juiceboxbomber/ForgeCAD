"""FreeCAD command for creating a ForgeCAD node from geometry."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.commands.draw_member_interactive import (
    existing_node_at_point,
    next_node_id,
)
from forgecad.adapters.freecad.commands.generate_nodes import (
    SOURCE_MANUAL,
    create_node_object,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


COMMAND_NAME = "ForgeCAD_CreateNodeFromGeometry"


def selected_vertex_points(
    selection_ex,
):
    """Return points from selected FreeCAD vertices."""

    points = []

    for selection in selection_ex:
        for subobject in selection.SubObjects:
            if (
                getattr(
                    subobject,
                    "ShapeType",
                    None,
                )
                != "Vertex"
            ):
                continue

            point = getattr(
                subobject,
                "Point",
                None,
            )

            if point is None:
                continue

            points.append(
                point
            )

    return points


def create_node_from_point(
    document,
    point,
):
    """
    Create a Manual ForgeCAD node at a geometry point.

    If a node already exists at the same coordinates,
    return the existing node instead.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    existing = existing_node_at_point(
        document,
        point,
    )

    if existing is not None:
        return existing, False

    groups = initialize_project_tree(
        document
    )

    nodes_group = groups[
        "Nodes"
    ]

    node_id = next_node_id(
        nodes_group
    )

    node_object = create_node_object(
        document,
        point,
        node_id,
        source_type=SOURCE_MANUAL,
    )

    nodes_group.addObject(
        node_object
    )

    document.recompute()

    return node_object, True


class CreateNodeFromGeometryCommand:
    """Create a ForgeCAD node from one selected FreeCAD vertex."""

    def GetResources(self):
        return {
            "MenuText":
                "Create Node From Geometry",
            "ToolTip": (
                "Create a persistent ForgeCAD node "
                "at one selected FreeCAD vertex"
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
                    "Open or create a FreeCAD "
                    "document first."
                ),
            )
            return

        points = selected_vertex_points(
            FreeCADGui.Selection.getSelectionEx()
        )

        if len(points) == 0:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Vertex Selected",
                (
                    "Select exactly one FreeCAD "
                    "vertex first."
                ),
            )
            return

        if len(points) > 1:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Multiple Vertices Selected",
                (
                    "Select only one FreeCAD vertex "
                    "for this command."
                ),
            )
            return

        try:
            node_object, created = (
                create_node_from_point(
                    document,
                    points[0],
                )
            )

        except ValueError as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Node Creation Failed",
                str(error),
            )
            return

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.Selection.addSelection(
            node_object
        )

        if not created:
            QtGui.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "Existing Node Reused",
                (
                    f"{node_object.NodeID} already "
                    "exists at this vertex."
                ),
            )

        FreeCADGui.activeDocument().activeView().fitAll()

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Create Node From Geometry command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        CreateNodeFromGeometryCommand(),
    )
    