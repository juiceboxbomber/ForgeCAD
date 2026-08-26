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
from forgecad.adapters.freecad.member_object import (
    ensure_member_node_links,
)
from forgecad.adapters.freecad.topology_refresh import (
    refresh_joint_topology,
)
from forgecad.adapters.freecad.fabrication_refresh import (
    refresh_fabrication_for_document,
)


COMMAND_NAME = "ForgeCAD_CreateMemberBetweenNodes"

POINT_PRECISION = 6


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


def point_key(
    point,
    precision=POINT_PRECISION,
):
    """Return a stable coordinate key for a FreeCAD-like point."""

    return (
        round(
            float(
                point.x
            ),
            precision,
        ),
        round(
            float(
                point.y
            ),
            precision,
        ),
        round(
            float(
                point.z
            ),
            precision,
        ),
    )


def layout_object_matches_points(
    layout_object,
    start_point,
    end_point,
):
    """
    Return True when a layout object connects the requested points.

    Connection direction is intentionally ignored so A-B and B-A
    identify the same physical layout member.
    """

    if (
        not hasattr(
            layout_object,
            "StartPoint",
        )
        or not hasattr(
            layout_object,
            "EndPoint",
        )
    ):
        return False

    requested_start = point_key(
        start_point
    )
    requested_end = point_key(
        end_point
    )

    existing_start = point_key(
        layout_object.StartPoint
    )
    existing_end = point_key(
        layout_object.EndPoint
    )

    return (
        (
            existing_start
            == requested_start
            and existing_end
            == requested_end
        )
        or (
            existing_start
            == requested_end
            and existing_end
            == requested_start
        )
    )


def existing_layout_object(
    layout_group,
    start_point,
    end_point,
):
    """Return an existing layout object joining the two points."""

    if layout_group is None:
        return None

    for obj in getattr(
        layout_group,
        "Group",
        [],
    ):
        if layout_object_matches_points(
            obj,
            start_point,
            end_point,
        ):
            return obj

    return None


def ensure_layout_object_between_nodes(
    document,
    layout_group,
    start_node,
    end_node,
):
    """
    Return a persistent layout object joining two domain nodes.

    Existing geometry is reused instead of creating a duplicate line.
    """

    start_point = FreeCAD.Vector(
        start_node.x,
        start_node.y,
        start_node.z,
    )

    end_point = FreeCAD.Vector(
        end_node.x,
        end_node.y,
        end_node.z,
    )

    layout_object = (
        existing_layout_object(
            layout_group,
            start_point,
            end_point,
        )
    )

    if layout_object is not None:
        ensure_layout_id(
            layout_object
        )
        return layout_object

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

    layout_object = (
        create_layout_line_object(
            document,
            layout_line,
        )
    )

    layout_group.addObject(
        layout_object
    )

    ensure_layout_id(
        layout_object
    )

    return layout_object


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
    profile=None,
    material=None,
    refresh=True,
):
    """
    Create a rendered tube between two ForgeCAD node objects.

    Existing matching layout geometry is reused so the command cannot
    create duplicate layout lines for the same physical connection.

    Optional profile/material arguments allow callers such as Mirror
    Members to preserve source-member properties. When omitted, the
    project active profile and default material are used exactly as
    before.

    refresh=False allows compound edit operations such as Split Member
    to create intermediate geometry without refreshing fabrication
    against a temporarily invalid topology. Normal callers retain the
    original refresh behavior.
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

    if profile is None:
        profile = (
            project.tube_library.active_profile
        )

    if material is None:
        material = (
            project.default_material
        )

    if profile is None:
        raise ValueError(
            "ForgeCAD project has no active tube profile."
        )

    if material is None:
        raise ValueError(
            "ForgeCAD project has no default material."
        )

    groups = initialize_project_tree(
        document
    )

    # -----------------------------------------------------
    # Persistent layout geometry
    # -----------------------------------------------------

    layout_object = (
        ensure_layout_object_between_nodes(
            document,
            groups[
                "Layout"
            ],
            start_node,
            end_node,
        )
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
        groups[
            "Frame"
        ]
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

    ensure_member_node_links(
        rendered_object,
        start_node_object,
        end_node_object,
    )

    groups[
        "Frame"
    ].addObject(
        rendered_object
    )

    document.recompute()

    if refresh:
        refresh_joint_topology(
            document
        )

        refresh_fabrication_for_document(
            document
        )

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

        transaction_started = False

        try:
            if hasattr(
                document,
                "openTransaction",
            ):
                document.openTransaction(
                    "Create ForgeCAD Member"
                )

                transaction_started = True

            layout_object, member_object = (
                create_member_between_nodes(
                    document,
                    selection[0],
                    selection[1],
                )
            )

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
            KeyError,
            RuntimeError,
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
                "Member Creation Failed",
                str(error),
            )
            return

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
