"""FreeCAD command for generating ForgeCAD nodes from layout lines."""

import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui

from forgecad.adapters.freecad.document_tree import (
    clear_group,
    initialize_project_tree,
)
from forgecad.adapters.freecad.commands.generate_from_selection import (
    selected_or_project_layout_lines,
)


COMMAND_NAME = "ForgeCAD_GenerateNodes"


def point_key(vector, precision=6):
    """Return a stable coordinate key for a FreeCAD vector."""

    return (
        round(float(vector.x), precision),
        round(float(vector.y), precision),
        round(float(vector.z), precision),
    )


def unique_layout_points(layout_objects):
    """Return unique StartPoint/EndPoint vectors from layout objects."""

    points = {}

    for obj in layout_objects:
        if not hasattr(
            obj,
            "StartPoint",
        ):
            continue

        if not hasattr(
            obj,
            "EndPoint",
        ):
            continue

        for point in (
            obj.StartPoint,
            obj.EndPoint,
        ):
            key = point_key(
                point
            )

            if key not in points:
                points[key] = point

    return list(
        points.values()
    )


def create_node_object(
    document,
    point,
    node_id,
):
    """Create one visible selectable ForgeCAD node object."""

    obj = document.addObject(
        "Part::Feature",
        "ForgeCADNode",
    )

    obj.Label = node_id

    obj.addProperty(
        "App::PropertyString",
        "NodeID",
        "ForgeCAD Node",
    )
    obj.NodeID = node_id

    obj.addProperty(
        "App::PropertyVector",
        "Position",
        "ForgeCAD Node",
    )
    obj.Position = point

    obj.addProperty(
        "App::PropertyFloat",
        "X",
        "ForgeCAD Node",
    )
    obj.X = float(
        point.x
    )

    obj.addProperty(
        "App::PropertyFloat",
        "Y",
        "ForgeCAD Node",
    )
    obj.Y = float(
        point.y
    )

    obj.addProperty(
        "App::PropertyFloat",
        "Z",
        "ForgeCAD Node",
    )
    obj.Z = float(
        point.z
    )

    # Small sphere used as a visible/selectable node marker.
    obj.Shape = Part.makeSphere(
        6.0,
        point,
    )

    try:
        obj.ViewObject.PointSize = 8.0
    except Exception:
        pass

    for property_name in (
        "NodeID",
        "Position",
        "X",
        "Y",
        "Z",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj


def generate_nodes_from_layout(
    document,
    layout_objects,
):
    """Generate unique FreeCAD nodes from layout endpoints."""

    points = unique_layout_points(
        layout_objects
    )

    groups = initialize_project_tree(
        document
    )

    nodes_group = groups[
        "Nodes"
    ]

    clear_group(
        document,
        nodes_group,
    )

    node_objects = []

    for index, point in enumerate(
        points,
        start=1,
    ):
        node_id = (
            f"N{index:03d}"
        )

        node_object = create_node_object(
            document,
            point,
            node_id,
        )

        nodes_group.addObject(
            node_object
        )

        node_objects.append(
            node_object
        )

    document.recompute()

    return node_objects


class GenerateNodesCommand:
    """Generate selectable nodes from ForgeCAD layout geometry."""

    def GetResources(self):
        return {
            "MenuText": "Generate Nodes",
            "ToolTip": (
                "Generate unique selectable ForgeCAD nodes "
                "from layout line endpoints"
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
                    "Create or draw a ForgeCAD "
                    "layout first."
                ),
            )
            return

        layout_objects = (
            selected_or_project_layout_lines(
                document
            )
        )

        if not layout_objects:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Layout Lines",
                (
                    "Draw or define one or more ForgeCAD "
                    "layout lines before generating nodes."
                ),
            )
            return

        node_objects = (
            generate_nodes_from_layout(
                document,
                layout_objects,
            )
        )

        if not node_objects:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Nodes Generated",
                (
                    "The selected layout objects did not "
                    "contain usable StartPoint/EndPoint data."
                ),
            )
            return

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.activeDocument().activeView().fitAll()

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Generate Nodes command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        GenerateNodesCommand(),
    )
    