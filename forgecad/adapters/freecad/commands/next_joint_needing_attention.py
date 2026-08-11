"""Navigate to the next ForgeCAD joint needing designer attention."""

import FreeCAD
import FreeCADGui
from PySide import QtGui


COMMAND_NAME = (
    "ForgeCAD_NextJointNeedingAttention"
)


def is_joint_status_object(
    obj,
):
    """Return True for a ForgeCAD Joints-tree status object."""

    if obj is None:
        return False

    required_properties = (
        "JointID",
        "NodeKey",
        "Position",
        "ReviewStatus",
        "NeedsAttention",
    )

    return all(
        hasattr(
            obj,
            property_name,
        )
        for property_name
        in required_properties
    )


def joint_status_objects(
    document,
):
    """Return Joints-tree objects in their current review order."""

    if document is None:
        return ()

    group = document.getObject(
        "ForgeCADJoints"
    )

    if group is None:
        return ()

    return tuple(
        obj
        for obj in group.Group
        if is_joint_status_object(
            obj
        )
    )


def attention_joint_objects(
    document,
):
    """Return only joints currently requiring attention."""

    return tuple(
        obj
        for obj in joint_status_objects(
            document
        )
        if bool(
            obj.NeedsAttention
        )
    )


def selected_joint_status_object(
    selection,
):
    """Return the selected Joints-tree object when exactly one exists."""

    selected_joint_objects = [
        obj
        for obj in selection
        if is_joint_status_object(
            obj
        )
    ]

    if len(
        selected_joint_objects
    ) != 1:
        return None

    return (
        selected_joint_objects[
            0
        ]
    )


def next_attention_joint(
    document,
    selection=(),
):
    """
    Return the next joint needing attention.

    When a Joints-tree item is currently selected, navigation
    continues forward from that object's position in the complete
    Joints list and wraps around once.

    When no Joints-tree item is selected, the first attention item
    is returned.
    """

    all_joints = (
        joint_status_objects(
            document
        )
    )

    if not all_joints:
        return None

    attention_joints = {
        id(obj)
        for obj in all_joints
        if bool(
            obj.NeedsAttention
        )
    }

    if not attention_joints:
        return None

    selected = (
        selected_joint_status_object(
            selection
        )
    )

    if (
        selected is None
        or selected not in all_joints
    ):
        for obj in all_joints:
            if id(
                obj
            ) in attention_joints:
                return obj

        return None

    start_index = (
        all_joints.index(
            selected
        )
        + 1
    )

    joint_count = len(
        all_joints
    )

    for offset in range(
        joint_count
    ):
        index = (
            start_index
            + offset
        ) % joint_count

        candidate = (
            all_joints[
                index
            ]
        )

        if id(
            candidate
        ) in attention_joints:
            return candidate

    return None


def select_joint_object(
    obj,
):
    """Select one joint-status object in the FreeCAD GUI."""

    FreeCADGui.Selection.clearSelection()

    FreeCADGui.Selection.addSelection(
        obj
    )


class NextJointNeedingAttentionCommand:
    """Select the next ForgeCAD joint requiring review."""

    def GetResources(
        self,
    ):
        return {
            "MenuText":
                "Next Joint Needing Attention",
            "ToolTip": (
                "Select the next unreviewed or invalid "
                "ForgeCAD joint"
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

        all_joints = (
            joint_status_objects(
                document
            )
        )

        if not all_joints:
            QtGui.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "No Frame Joints",
                (
                    "Generate a ForgeCAD frame before "
                    "reviewing joints."
                ),
            )
            return

        selection = tuple(
            FreeCADGui.Selection.getSelection()
        )

        next_joint = (
            next_attention_joint(
                document,
                selection,
            )
        )

        if next_joint is None:
            QtGui.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "Joint Review Complete",
                (
                    "All frame joints have been reviewed "
                    "and no invalid treatments remain."
                ),
            )
            return

        select_joint_object(
            next_joint
        )

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the command with FreeCAD."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        NextJointNeedingAttentionCommand(),
    )
    