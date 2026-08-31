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
from forgecad.geometry import point
from forgecad.adapters.freecad.node_object import (
    create_node_object as create_parametric_node_object,
    ensure_node_proxy,
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


def point_on_segment(
    point,
    start,
    end,
    tolerance=1e-6,
):
    """
    Return True when point lies on the finite 3D segment start-end.

    This uses vector projection rather than axis-specific comparisons,
    so it works for layout lines in any 3D orientation.
    """

    segment_x = float(
        end.x - start.x
    )
    segment_y = float(
        end.y - start.y
    )
    segment_z = float(
        end.z - start.z
    )

    point_x = float(
        point.x - start.x
    )
    point_y = float(
        point.y - start.y
    )
    point_z = float(
        point.z - start.z
    )

    length_squared = (
        segment_x * segment_x
        + segment_y * segment_y
        + segment_z * segment_z
    )

    if length_squared <= (
        tolerance * tolerance
    ):
        return False

    parameter = (
        point_x * segment_x
        + point_y * segment_y
        + point_z * segment_z
    ) / length_squared

    if (
        parameter < -tolerance
        or parameter > 1.0 + tolerance
    ):
        return False

    parameter = max(
        0.0,
        min(
            1.0,
            parameter,
        ),
    )

    nearest_x = (
        float(start.x)
        + parameter * segment_x
    )
    nearest_y = (
        float(start.y)
        + parameter * segment_y
    )
    nearest_z = (
        float(start.z)
        + parameter * segment_z
    )

    delta_x = (
        float(point.x)
        - nearest_x
    )
    delta_y = (
        float(point.y)
        - nearest_y
    )
    delta_z = (
        float(point.z)
        - nearest_z
    )

    distance_squared = (
        delta_x * delta_x
        + delta_y * delta_y
        + delta_z * delta_z
    )

    return distance_squared <= (
        tolerance * tolerance
    )

def layout_objects_for_point(
    point,
    layout_objects,
):
    """
    Return layout objects whose finite segment contains the point.

    This includes both endpoint connections and interior connections such
    as T-junctions. Continuous through-lines are referenced but not split.
    """

    result = []

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

        if not point_on_segment(
            point,
            obj.StartPoint,
            obj.EndPoint,
        ):
            continue

        result.append(
            obj
        )

    return result

def ensure_source_layout_objects(
    obj,
    layout_objects,
):
    """
    Ensure a ForgeCAD node stores references to its source layout objects.
    """

    if not hasattr(
        obj,
        "SourceLayoutLines",
    ):
        obj.addProperty(
            "App::PropertyLinkList",
            "SourceLayoutLines",
            "ForgeCAD Node",
        )

    obj.SourceLayoutLines = list(
        layout_objects
    )

    try:
        obj.setEditorMode(
            "SourceLayoutLines",
            1,
        )
    except Exception:
        pass

    return list(
        obj.SourceLayoutLines
    )


def canonical_layout_point(
    point,
    layout_objects,
):
    """
    Return the exact stored segment position for a layout connection.

    A snapped branch endpoint may lie on the interior of another
    layout line. Re-projecting it onto that line gives node generation
    one stable coordinate for the shared connection without splitting
    the continuous layout line.
    """

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

        start = obj.StartPoint
        end = obj.EndPoint

        if not point_on_segment(
            point,
            start,
            end,
        ):
            continue

        segment_x = float(
            end.x - start.x
        )
        segment_y = float(
            end.y - start.y
        )
        segment_z = float(
            end.z - start.z
        )

        length_squared = (
            segment_x * segment_x
            + segment_y * segment_y
            + segment_z * segment_z
        )

        if length_squared <= 1e-12:
            continue

        parameter = (
            float(
                point.x - start.x
            ) * segment_x
            + float(
                point.y - start.y
            ) * segment_y
            + float(
                point.z - start.z
            ) * segment_z
        ) / length_squared

        parameter = max(
            0.0,
            min(
                1.0,
                parameter,
            ),
        )

        try:
            return type(point)(
                float(start.x)
                + parameter * segment_x,
                float(start.y)
                + parameter * segment_y,
                float(start.z)
                + parameter * segment_z,
            )
        except Exception:
            return point

    return point


def unique_layout_points(
    layout_objects,
):
    """
    Return unique layout endpoints, including interior connections.

    Layout lines remain continuous. When one line endpoint lies on
    another line's interior, the shared point becomes a node location.
    """

    objects = [
        obj
        for obj in layout_objects
        if (
            hasattr(
                obj,
                "StartPoint",
            )
            and hasattr(
                obj,
                "EndPoint",
            )
        )
    ]

    points = {}

    for obj in objects:
        for point in (
            obj.StartPoint,
            obj.EndPoint,
        ):
            resolved_point = (
                canonical_layout_point(
                    point,
                    objects,
                )
            )

            key = point_key(
                resolved_point
            )

            if key not in points:
                points[key] = (
                    resolved_point
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
    """
    Create one parametric ForgeCAD node object.

    This wrapper preserves the existing public import location used by
    other ForgeCAD commands while node behavior lives in node_object.py.
    """

    return create_parametric_node_object(
        document,
        point,
        node_id,
        source_type=source_type,
    )


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
    # Migrate existing nodes to parametric node behavior
    # -----------------------------------------------------

    for existing_node in node_objects(
        nodes_group
    ):
        ensure_node_proxy(
            existing_node
        )

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
        source_layout_objects = (
            layout_objects_for_point(
                point,
                layout_objects,
            )
        )

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

                ensure_source_layout_objects(
                    existing,
                    source_layout_objects,
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

        ensure_source_layout_objects(
            node_object,
            source_layout_objects,
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

        transaction_started = False

        try:
            if hasattr(
                document,
                "openTransaction",
            ):
                document.openTransaction(
                    "Generate ForgeCAD Nodes"
                )

                transaction_started = True

            node_objects = (
                generate_nodes_from_layout(
                    document,
                    layout_objects,
                )
            )

            if not node_objects:
                if (
                    transaction_started
                    and hasattr(
                        document,
                        "abortTransaction",
                    )
                ):
                    try:
                        document.abortTransaction()
                    except Exception:
                        pass

                QtGui.QMessageBox.warning(
                    FreeCADGui.getMainWindow(),
                    "No Nodes Generated",
                    (
                        "The selected layout objects did not "
                        "contain usable StartPoint/EndPoint data."
                    ),
                )
                return

            if (
                transaction_started
                and hasattr(
                    document,
                    "commitTransaction",
                )
            ):
                document.commitTransaction()

        except (
            ValueError,
            RuntimeError,
            KeyError,
            AttributeError,
        ) as error:
            if (
                transaction_started
                and hasattr(
                    document,
                    "abortTransaction",
                )
            ):
                try:
                    document.abortTransaction()
                except Exception:
                    pass

            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Node Generation Failed",
                str(
                    error
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
    