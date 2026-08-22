"""FreeCAD command for safely deleting one ForgeCAD straight member."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.fabrication_refresh import refresh_fabrication_for_document
from forgecad.adapters.freecad.member_removal import remove_member_and_unused_layout
from forgecad.adapters.freecad.node_cleanup import remove_node_if_unused
from forgecad.adapters.freecad.topology_refresh import refresh_joint_topology

COMMAND_NAME = "ForgeCAD_DeleteMember"


def is_forgecad_member(obj):
    """Return True when an object is a generated ForgeCAD straight member."""

    if obj is None:
        return False

    return (
        hasattr(obj, "MemberID")
        and hasattr(obj, "SourceLayoutID")
    )


def endpoint_nodes(member_object):
    """Return unique persistent endpoint nodes linked to a member."""

    nodes = []

    for property_name in (
        "StartNode",
        "EndNode",
    ):
        node = getattr(
            member_object,
            property_name,
            None,
        )

        if node is not None and node not in nodes:
            nodes.append(node)

    return tuple(nodes)


def delete_member(
    document,
    member_object,
):
    """Safely delete one generated ForgeCAD straight member."""

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if not is_forgecad_member(
        member_object
    ):
        raise ValueError(
            "The selected object is not a ForgeCAD straight member."
        )

    nodes = endpoint_nodes(
        member_object
    )

    removed = remove_member_and_unused_layout(
        document,
        member_object,
    )

    if not removed:
        raise RuntimeError(
            "ForgeCAD could not remove the selected member."
        )

    for node in nodes:
        remove_node_if_unused(
            document,
            node,
        )

    document.recompute()

    refresh_joint_topology(
        document
    )

    refresh_fabrication_for_document(
        document
    )

    document.recompute()

    return True


class DeleteMemberCommand:
    """Safely delete one selected ForgeCAD straight member."""

    def GetResources(self):
        return {
            "MenuText": "Delete Member",
            "ToolTip": (
                "Delete one selected ForgeCAD member and "
                "clean up unused layout, nodes, and joint state"
            ),
        }

    def Activated(self):
        document = FreeCAD.ActiveDocument

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Document",
                "Open or create a ForgeCAD project first.",
            )
            return

        selection = list(
            FreeCADGui.Selection.getSelection()
        )

        if len(selection) != 1:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select One Member",
                "Select exactly one ForgeCAD straight member to delete.",
            )
            return

        member_object = selection[0]

        if not is_forgecad_member(
            member_object
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                "The selected object is not a ForgeCAD straight member.",
            )
            return

        try:
            delete_member(
                document,
                member_object,
            )
        except (
            ValueError,
            RuntimeError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Delete Member Failed",
                str(error),
            )
            return

        FreeCADGui.Selection.clearSelection()

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


def register_command() -> None:
    """Register the Delete Member command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        DeleteMemberCommand(),
    )
