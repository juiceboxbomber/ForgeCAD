"""FreeCAD command for safely deleting one ForgeCAD bent tube."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.fabrication_refresh import (
    refresh_fabrication_for_document,
)
from forgecad.adapters.freecad.node_cleanup import (
    remove_node_if_unused,
)
from forgecad.adapters.freecad.topology_refresh import (
    refresh_joint_topology,
)


COMMAND_NAME = "ForgeCAD_DeleteBentTube"


def bent_tube_objects(
    document,
):
    """Return persistent ForgeCAD bent-tube objects."""

    if document is None:
        return ()

    group = document.getObject(
        "ForgeCADBentTubes"
    )

    if group is None:
        return ()

    return tuple(
        getattr(
            group,
            "Group",
            (),
        )
    )


def is_forgecad_bent_tube(
    document,
    obj,
):
    """Return True when an object belongs to ForgeCAD Bent Tubes."""

    if (
        document is None
        or obj is None
    ):
        return False

    return obj in bent_tube_objects(
        document
    )


def endpoint_nodes(
    bent_tube_object,
):
    """Return unique persistent endpoint nodes linked to a bent tube."""

    nodes = []

    for property_name in (
        "StartNode",
        "EndNode",
    ):
        node = getattr(
            bent_tube_object,
            property_name,
            None,
        )

        if (
            node is not None
            and node not in nodes
        ):
            nodes.append(
                node
            )

    return tuple(
        nodes
    )


def remove_object_from_group(
    group,
    obj,
):
    """Detach an object from its containing group when possible."""

    if (
        group is None
        or obj is None
    ):
        return

    try:
        group.removeObject(
            obj
        )
    except Exception:
        pass


def delete_bent_tube(
    document,
    bent_tube_object,
):
    """
    Safely delete one ForgeCAD bent tube.

    Bent tubes have no straight source-layout object. Their endpoint nodes
    are removed only when no remaining object references them. Joint and
    fabrication state are rebuilt after removal.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if not is_forgecad_bent_tube(
        document,
        bent_tube_object,
    ):
        raise ValueError(
            "The selected object is not a ForgeCAD bent tube."
        )

    object_name = str(
        getattr(
            bent_tube_object,
            "Name",
            "",
        )
    ).strip()

    if not object_name:
        raise ValueError(
            "ForgeCAD bent tube has no document object name."
        )

    nodes = endpoint_nodes(
        bent_tube_object
    )

    group = document.getObject(
        "ForgeCADBentTubes"
    )

    remove_object_from_group(
        group,
        bent_tube_object,
    )

    document.removeObject(
        object_name
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


class DeleteBentTubeCommand:
    """Safely delete one selected ForgeCAD bent tube."""

    def GetResources(
        self,
    ):
        return {
            "MenuText":
                "Delete Bent Tube",
            "ToolTip": (
                "Delete one selected ForgeCAD bent tube and "
                "clean up unused endpoint nodes and joint state"
            ),
        }

    def Activated(
        self,
    ):
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

        if len(
            selection
        ) != 1:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select One Bent Tube",
                (
                    "Select exactly one ForgeCAD bent tube "
                    "to delete."
                ),
            )
            return

        bent_tube_object = (
            selection[
                0
            ]
        )

        if not is_forgecad_bent_tube(
            document,
            bent_tube_object,
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                (
                    "The selected object is not "
                    "a ForgeCAD bent tube."
                ),
            )
            return

        try:
            delete_bent_tube(
                document,
                bent_tube_object,
            )

        except (
            ValueError,
            RuntimeError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Delete Bent Tube Failed",
                str(
                    error
                ),
            )
            return

        FreeCADGui.Selection.clearSelection()

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Delete Bent Tube command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        DeleteBentTubeCommand(),
    )
