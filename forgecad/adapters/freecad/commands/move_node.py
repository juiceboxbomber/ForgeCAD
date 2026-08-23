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
        float(
            base.x
        ),
        float(
            base.y
        ),
        float(
            base.z
        ),
    )


def preview_node_position(
    document,
    node,
    x,
    y,
    z,
):
    """
    Move a node for live visual preview without rebuilding joint topology.

    The normal node proxy updates coordinate mirrors, layout endpoints,
    and connected-member dependencies. A document recompute then redraws
    the connected member geometry while the dialog remains open.
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
        float(
            x
        ),
        float(
            y
        ),
        float(
            z
        ),
    )

    document.recompute()

    return node


def move_node(
    document,
    node,
    x,
    y,
    z,
):
    """
    Commit one ForgeCAD node to an absolute XYZ position.

    Placement is the authoritative editable location. The node proxy owns
    synchronization of Position/XYZ mirrors, layout endpoints, constraints,
    and connected member dependencies. Joint topology is refreshed only
    after the committed geometry has recomputed.
    """

    moved_node = preview_node_position(
        document,
        node,
        x,
        y,
        z,
    )

    from forgecad.adapters.freecad.topology_refresh import (
        refresh_joint_topology,
    )

    refresh_joint_topology(
        document
    )

    document.recompute()

    return moved_node


class MoveNodeDialog(
    QtGui.QDialog
):
    """Edit one ForgeCAD node with live XYZ preview."""

    def __init__(
        self,
        document,
        node,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.document = document
        self.node = node

        current = node_position(
            node
        )

        self.original_position = (
            float(
                current.x
            ),
            float(
                current.y
            ),
            float(
                current.z
            ),
        )

        self._restoring = False

        self.setWindowTitle(
            "Move Node"
        )

        self.setMinimumWidth(
            360
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

        live_note = (
            QtGui.QLabel(
                "Geometry updates live while you change X, Y, or Z. "
                "Cancel restores the original position."
            )
        )

        live_note.setWordWrap(
            True
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

        layout.addWidget(
            live_note
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

        self.x_position.valueChanged.connect(
            self.update_live_preview
        )

        self.y_position.valueChanged.connect(
            self.update_live_preview
        )

        self.z_position.valueChanged.connect(
            self.update_live_preview
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

    def update_live_preview(
        self,
        *args,
    ):
        """Recompute connected geometry while coordinate values change."""

        if self._restoring:
            return

        try:
            preview_node_position(
                self.document,
                self.node,
                self.x_position.value(),
                self.y_position.value(),
                self.z_position.value(),
            )

        except ValueError:
            return

    def restore_original_position(
        self,
    ):
        """Restore the node to its position from when the dialog opened."""

        if self._restoring:
            return

        self._restoring = True

        try:
            (
                x,
                y,
                z,
            ) = self.original_position

            preview_node_position(
                self.document,
                self.node,
                x,
                y,
                z,
            )

        finally:
            self._restoring = False

    def reject(
        self,
    ):
        """Cancel the edit and restore the original geometry."""

        self.restore_original_position()

        super().reject()


class MoveNodeCommand:
    """Move one selected ForgeCAD node with live visual feedback."""

    def GetResources(
        self,
    ):
        return {
            "MenuText":
                "Move Node",
            "ToolTip": (
                "Move one selected ForgeCAD node with "
                "live connected-member preview"
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

        ensure_node_proxy(
            node
        )

        dialog = MoveNodeDialog(
            document,
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
