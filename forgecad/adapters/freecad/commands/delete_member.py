"""FreeCAD command for safely deleting one ForgeCAD structural member."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.fabrication_refresh import refresh_fabrication_for_document
from forgecad.adapters.freecad.joint_inspector_adapter import (
    is_forgecad_bent_member,
)
from forgecad.adapters.freecad.member_removal import (
    remove_bent_member_and_unused_layouts,
    remove_member_and_unused_layout,
)
from forgecad.adapters.freecad.node_cleanup import remove_node_if_unused
from forgecad.adapters.freecad.topology_refresh import refresh_joint_topology

COMMAND_NAME = "ForgeCAD_DeleteMember"


def is_forgecad_member(obj):
    if obj is None:
        return False

    return (
        (
            hasattr(obj, "MemberID")
            and hasattr(obj, "SourceLayoutID")
        )
        or is_forgecad_bent_member(obj)
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


def design_joint_nodes(member_object):
    nodes = []

    legacy = getattr(member_object, "DesignJointNode", None)
    if legacy is not None:
        nodes.append(legacy)

    index = 1
    while True:
        property_name = f"DesignJointNode{index}"
        if not hasattr(member_object, property_name):
            break

        node = getattr(member_object, property_name, None)
        if node is not None and node not in nodes:
            nodes.append(node)

        index += 1

    return tuple(nodes)

def delete_member(
    document,
    member_object,
):
    if document is None:
        raise ValueError("A FreeCAD document is required.")

    if not is_forgecad_member(member_object):
        raise ValueError("The selected object is not a ForgeCAD member.")

    nodes = list(endpoint_nodes(member_object))
    bent = is_forgecad_bent_member(member_object)

    if bent:
        for node in design_joint_nodes(member_object):
            if node not in nodes:
                nodes.append(node)

        removed = remove_bent_member_and_unused_layouts(
            document,
            member_object,
        )
    else:
        removed = remove_member_and_unused_layout(
            document,
            member_object,
        )

    if not removed:
        raise RuntimeError("ForgeCAD could not remove the selected member.")

    for node in nodes:
        remove_node_if_unused(document, node)

    document.recompute()
    refresh_joint_topology(document)
    refresh_fabrication_for_document(document)
    document.recompute()

    return True



def begin_delete_transaction(document):
    """Open one Undo transaction for a complete Delete Member operation."""

    if (
        document is None
        or not hasattr(document, "openTransaction")
    ):
        return False

    document.openTransaction(
        "Delete ForgeCAD Member"
    )

    return True


def finish_delete_transaction(
    document,
    transaction_started,
):
    """Commit a Delete Member Undo transaction."""

    if (
        transaction_started
        and hasattr(document, "commitTransaction")
    ):
        document.commitTransaction()


def abort_delete_transaction(
    document,
    transaction_started,
):
    """Abort a failed Delete Member Undo transaction."""

    if (
        not transaction_started
        or not hasattr(document, "abortTransaction")
    ):
        return

    try:
        document.abortTransaction()
    except Exception:
        pass


class DeleteMemberCommand:
    """Safely delete one selected ForgeCAD structural member."""

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
                "Select exactly one ForgeCAD member to delete.",
            )
            return

        member_object = selection[0]

        if not is_forgecad_member(
            member_object
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                "The selected object is not a ForgeCAD member.",
            )
            return

        transaction_started = False

        try:
            transaction_started = (
                begin_delete_transaction(
                    document
                )
            )

            delete_member(
                document,
                member_object,
            )

            finish_delete_transaction(
                document,
                transaction_started,
            )

        except (
            ValueError,
            RuntimeError,
            KeyError,
            AttributeError,
        ) as error:
            abort_delete_transaction(
                document,
                transaction_started,
            )

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
