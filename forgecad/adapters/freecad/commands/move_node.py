"""FreeCAD command for moving one existing ForgeCAD node."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.node_object import (
    ensure_node_proxy,
)


COMMAND_NAME = "ForgeCAD_MoveNode"


def is_forgecad_node(
    obj,
):
    """Return True when an object is a ForgeCAD node."""

    if obj is None:
        return False

    required_properties = (
        "NodeID",
        "Position",
        "Placement",
    )

    return all(
        hasattr(
            obj,
            property_name,
        )
        for property_name in required_properties
    )


def node_position(
    node,
):
    """Return the authoritative current node position."""

    base = node.Placement.Base

    return FreeCAD.Vector(
        float(base.x),
        float(base.y),
        float(base.z),
    )


def move_node(
    document,
    node,
    x,
    y,
    z,
):
    """
    Move one ForgeCAD node to an absolute XYZ position.

    Placement is the authoritative editable location. The node proxy owns
    synchronization of Position/XYZ mirrors, layout endpoints, constraints,
    and connected member dependencies.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if not is_forgecad_node(
        node
    ):
        raise ValueError(
            "The selected object is not a ForgeCAD node."
        )

    ensure_node_proxy(
        node
    )

    node.Placement.Base = FreeCAD.Vector(
        float(x),
        float(y),
        float(z),
    )

    document.recompute()

    from forgecad.adapters.freecad.topology_refresh import (
        refresh_joint_topology,
    )

    refresh_joint_topology(
        document
    )

    document.recompute()

    return node


class MoveNodeDialog(
    QtGui.QDialog
):
    """Collect an absolute XYZ position for one ForgeCAD node."""

    def __init__(
        self,
        node,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.node = node

        self.setWindowTitle(
            "Move Node"
        )

        self.setMinimumWidth(
            360
        )

        current = node_position(
            node
        )

        self.node_id = (
            QtGui.QLineEdit()
        )

        self.node_id.setText(
            str(
                node.NodeID
            )
        )

        self.node_id.setReadOnly(
            True
        )

        self.x_position = (
            self.create_position_box(
                current.x
            )
        )

        self.y_position = (
            self.create_position_box(
                current.y
            )
        )

        self.z_position = (
            self.create_position_box(
                current.z
            )
        )

        form = (
            QtGui.QFormLayout()
        )

        form.addRow(
            "Node:",
            self.node_id,
        )

        form.addRow(
            "X (mm):",
            self.x_position,
        )

        form.addRow(
            "Y (mm):",
            self.y_position,
        )

        form.addRow(
            "Z (mm):",
            self.z_position,
        )

        buttons = (
            QtGui.QDialogButtonBox(
                QtGui.QDialogButtonBox.Ok
                | QtGui.QDialogButtonBox.Cancel
            )
        )

        buttons.button(
            QtGui.QDialogButtonBox.Ok
        ).setText(
            "Move"
        )

        buttons.accepted.connect(
            self.accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout = (
            QtGui.QVBoxLayout()
        )

        layout.addLayout(
            form
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            buttons
        )

        self.setLayout(
            layout
        )

        self.x_position.setFocus()

        try:
            self.x_position.selectAll()
        except Exception:
            pass

    @staticmethod
    def create_position_box(
        value,
    ):
        """Create one absolute millimeter coordinate input."""

        box = (
            QtGui.QDoubleSpinBox()
        )

        box.setRange(
            -1_000_000.0,
            1_000_000.0,
        )

        box.setDecimals(
            3
        )

        box.setSingleStep(
            10.0
        )

        box.setValue(
            float(
                value
            )
        )

        return box


class MoveNodeCommand:
    """Move one selected ForgeCAD node to an absolute XYZ position."""

    def GetResources(
        self,
    ):
        return {
            "MenuText":
                "Move Node",
            "ToolTip": (
                "Move one selected ForgeCAD node "
                "to a new X, Y, Z position"
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
                "Select One Node",
                (
                    "Select exactly one ForgeCAD node "
                    "to move."
                ),
            )
            return

        node = selection[
            0
        ]

        if not is_forgecad_node(
            node
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                (
                    "The selected object is not "
                    "a ForgeCAD node."
                ),
            )
            return

        dialog = MoveNodeDialog(
            node,
            FreeCADGui.getMainWindow(),
        )

        if (
            dialog.exec_()
            != QtGui.QDialog.Accepted
        ):
            return

        try:
            moved_node = move_node(
                document,
                node,
                dialog.x_position.value(),
                dialog.y_position.value(),
                dialog.z_position.value(),
            )

        except ValueError as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Move Node Failed",
                str(
                    error
                ),
            )
            return

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.Selection.addSelection(
            moved_node
        )

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Move Node command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        MoveNodeCommand(),
    )
