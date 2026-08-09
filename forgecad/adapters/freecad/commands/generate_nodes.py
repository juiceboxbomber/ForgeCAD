"""FreeCAD command for generating ForgeCAD nodes from layout lines."""

import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui

from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)
from forgecad.adapters.freecad.commands.generate_from_selection import (
    selected_or_project_layout_lines,
)


COMMAND_NAME = "ForgeCAD_GenerateNodes"

SOURCE_LAYOUT = "Layout"
SOURCE_MANUAL = "Manual"


def point_key(
    vector,
    precision=6,
):
    """Return a stable coordinate key for a FreeCAD vector."""

    return (
        round(
            float(vector.x),
            precision,
        ),
        round(
            float(vector.y),
            precision,
        ),
        round(
            float(vector.z),
            precision,
        ),
    )


def unique_layout_points(
    layout_objects,
):
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
                points[key] = (
                    point
                )

    return list(
        points.values()
    )


def ensure_source_type(
    obj,
    source_type,
):
    """Ensure a ForgeCAD node stores its source classification."""

    if not hasattr(
        obj,
        "SourceType",
    ):
        obj.addProperty(
            "App::PropertyString",
            "SourceType",
            "ForgeCAD Node",
        )

    obj.SourceType = str(
        source_type
    )

    try:
        obj.setEditorMode(
            "SourceType",
            1,
        )
    except Exception:
        pass

    return obj.SourceType


def create_node_object(
    document,
    point,
    node_id,
    source_type=SOURCE_MANUAL,
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

    obj.addProperty(
        "App::PropertyString",
        "SourceType",
        "ForgeCAD Node",
    )
    obj.SourceType = str(
        source_type
    )

    # Small sphere used as a visible/selectable node marker.
    obj.Shape = Part.makeSphere(
        6.0,
        point,
    )

    try:
        obj.ViewObject.PointSize = (
            8.0
        )
    except Exception:
        pass

    for property_name in (
        "NodeID",
        "Position",
        "X",
        "Y",
        "Z",
        "SourceType",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj


def node_objects(
    nodes_group,
):
    """Return valid ForgeCAD node objects in the Nodes group."""

    result = []

    for obj in nodes_group.Group:
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

        result.append(
            obj
        )

    return result


def node_by_point(
    nodes_group,
    point,
):
    """Return an existing node at the requested coordinates."""

    target_key = point_key(
        point
    )

    for obj in node_objects(
        nodes_group
    ):
        if point_key(
            obj.Position
        ) == target_key:
            return obj

    return None


def next_node_id(
    nodes_group,
):
    """Return the next unused ForgeCAD node ID."""

    highest_number = 0

    for obj in node_objects(
        nodes_group
    ):
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


def migrate_existing_node_sources(
    nodes_group,
    layout_points,
):
    """
    Add SourceType to nodes created before source tracking existed.

    Existing nodes matching current layout endpoints are treated as
    Layout nodes. Other existing nodes are preserved as Manual nodes.
    """

    layout_keys = {
        point_key(
            point
        )
        for point in layout_points
    }

    for obj in node_objects(
        nodes_group
    ):
        if hasattr(
            obj,
            "SourceType",
        ):
            source_type = str(
                obj.SourceType
            ).strip()

            if source_type in (
                SOURCE_LAYOUT,
                SOURCE_MANUAL,
            ):
                continue

        node_key = point_key(
            obj.Position
        )

        if node_key in layout_keys:
            source_type = (
                SOURCE_LAYOUT
            )
        else:
            source_type = (
                SOURCE_MANUAL
            )

        ensure_source_type(
            obj,
            source_type,
        )


def remove_obsolete_layout_nodes(
    document,
    nodes_group,
    layout_points,
):
    """Remove Layout nodes that are no longer layout endpoints."""

    layout_keys = {
        point_key(
            point
        )
        for point in layout_points
    }

    objects_to_remove = []

    for obj in node_objects(
        nodes_group
    ):
        source_type = str(
            getattr(
                obj,
                "SourceType",
                "",
            )
        ).strip()

        if (
            source_type
            != SOURCE_LAYOUT
        ):
            continue

        if point_key(
            obj.Position
        ) in layout_keys:
            continue

        objects_to_remove.append(
            obj
        )

    for obj in objects_to_remove:
        try:
            nodes_group.removeObject(
                obj
            )
        except Exception:
            pass

        try:
            document.removeObject(
                obj.Name
            )
        except Exception:
            pass


def generate_nodes_from_layout(
    document,
    layout_objects,
):
    """
    Synchronize Layout nodes with layout endpoints.

    Manual nodes are preserved.
    Existing nodes at matching coordinates are reused.
    """

    points = unique_layout_points(
        layout_objects
    )

    groups = initialize_project_tree(
        document
    )

    nodes_group = groups[
        "Nodes"
    ]

    # -----------------------------------------------------
    # Migrate nodes created before SourceType existed
    # -----------------------------------------------------

    migrate_existing_node_sources(
        nodes_group,
        points,
    )

    # -----------------------------------------------------
    # Remove only obsolete layout-derived nodes
    # -----------------------------------------------------

    remove_obsolete_layout_nodes(
        document,
        nodes_group,
        points,
    )

    # -----------------------------------------------------
    # Synchronize current layout endpoints
    # -----------------------------------------------------

    layout_node_objects = []

    for point in points:
        existing = node_by_point(
            nodes_group,
            point,
        )

        if existing is not None:
            # If a Manual node already occupies this exact point,
            # reuse it rather than creating a duplicate. Its Manual
            # classification is intentionally preserved.
            if str(
                getattr(
                    existing,
                    "SourceType",
                    "",
                )
            ).strip() == SOURCE_LAYOUT:
                ensure_source_type(
                    existing,
                    SOURCE_LAYOUT,
                )

            layout_node_objects.append(
                existing
            )

            continue

        node_id = next_node_id(
            nodes_group
        )

        node_object = create_node_object(
            document,
            point,
            node_id,
            source_type=SOURCE_LAYOUT,
        )

        nodes_group.addObject(
            node_object
        )

        layout_node_objects.append(
            node_object
        )

    document.recompute()

    return layout_node_objects


class GenerateNodesCommand:
    """Generate selectable nodes from ForgeCAD layout geometry."""

    def GetResources(self):
        return {
            "MenuText": "Generate Nodes",
            "ToolTip": (
                "Synchronize layout-derived ForgeCAD nodes "
                "while preserving manual construction nodes"
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
    