"""FreeCAD command for creating a ForgeCAD node by XYZ offset."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.commands.draw_member_interactive import (
    existing_node_at_point,
    next_node_id,
)
from forgecad.adapters.freecad.commands.generate_nodes import (
    create_node_object,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


COMMAND_NAME = "ForgeCAD_CreateOffsetNode"


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
        for property_name in required_properties
    )


def offset_point(
    base_point,
    x_offset,
    y_offset,
    z_offset,
):
    """Return a new FreeCAD vector offset from a base point."""

    return FreeCAD.Vector(
        float(base_point.x)
        + float(x_offset),
        float(base_point.y)
        + float(y_offset),
        float(base_point.z)
        + float(z_offset),
    )


def create_offset_node(
    document,
    source_node,
    x_offset,
    y_offset,
    z_offset,
):
    """
    Create a node at an XYZ offset from an existing node.

    If a node already exists at the target coordinates,
    return that existing node instead.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if not is_forgecad_node(
        source_node
    ):
        raise ValueError(
            "The source object is not a ForgeCAD node."
        )

    target_point = offset_point(
        source_node.Position,
        x_offset,
        y_offset,
        z_offset,
    )

    existing = existing_node_at_point(
        document,
        target_point,
    )

    if existing is not None:
        return existing, False

    groups = initialize_project_tree(
        document
    )

    nodes_group = groups[
        "Nodes"
    ]

    node_id = next_node_id(
        nodes_group
    )

    node_object = create_node_object(
        document,
        target_point,
        node_id,
    )

    nodes_group.addObject(
        node_object
    )

    document.recompute()

    return node_object, True


class OffsetNodeDialog(QtGui.QDialog):
    """Collect XYZ offsets for a new ForgeCAD node."""

    def __init__(
        self,
        source_node,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.source_node = (
            source_node
        )

        self.setWindowTitle(
            "Create Offset Node"
        )

        self.setMinimumWidth(
            400
        )

        # -------------------------------------------------
        # Source information
        # -------------------------------------------------

        self.source_id = (
            QtGui.QLineEdit()
        )

        self.source_id.setText(
            str(
                source_node.NodeID
            )
        )

        self.source_id.setReadOnly(
            True
        )

        position = (
            source_node.Position
        )

        self.source_position = (
            QtGui.QLineEdit()
        )

        self.source_position.setText(
            (
                f"X {float(position.x):.3f}, "
                f"Y {float(position.y):.3f}, "
                f"Z {float(position.z):.3f} mm"
            )
        )

        self.source_position.setReadOnly(
            True
        )

        # -------------------------------------------------
        # Offset controls
        # -------------------------------------------------

        self.x_offset = (
            self.create_offset_box()
        )

        self.y_offset = (
            self.create_offset_box()
        )

        self.z_offset = (
            self.create_offset_box()
        )

        self.x_offset.valueChanged.connect(
            self.update_target
        )

        self.y_offset.valueChanged.connect(
            self.update_target
        )

        self.z_offset.valueChanged.connect(
            self.update_target
        )

        # -------------------------------------------------
        # Target preview
        # -------------------------------------------------

        self.target_position = (
            QtGui.QLineEdit()
        )

        self.target_position.setReadOnly(
            True
        )

        # -------------------------------------------------
        # Form
        # -------------------------------------------------

        form = (
            QtGui.QFormLayout()
        )

        form.addRow(
            "Source Node:",
            self.source_id,
        )

        form.addRow(
            "Source Position:",
            self.source_position,
        )

        form.addRow(
            "X Offset (mm):",
            self.x_offset,
        )

        form.addRow(
            "Y Offset (mm):",
            self.y_offset,
        )

        form.addRow(
            "Z Offset (mm):",
            self.z_offset,
        )

        form.addRow(
            "Target Position:",
            self.target_position,
        )

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------

        buttons = (
            QtGui.QDialogButtonBox(
                QtGui.QDialogButtonBox.Ok
                | QtGui.QDialogButtonBox.Cancel
            )
        )

        buttons.button(
            QtGui.QDialogButtonBox.Ok
        ).setText(
            "Create Node"
        )

        buttons.accepted.connect(
            self.accept
        )

        buttons.rejected.connect(
            self.reject
        )

        # -------------------------------------------------
        # Main layout
        # -------------------------------------------------

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

        self.update_target()

        # Z is useful immediately for chassis uprights.
        self.z_offset.setFocus()

    @staticmethod
    def create_offset_box():
        """Create one millimeter offset input."""

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
            0.0
        )

        return box

    def target_point(self):
        """Return the currently requested target point."""

        return offset_point(
            self.source_node.Position,
            self.x_offset.value(),
            self.y_offset.value(),
            self.z_offset.value(),
        )

    def update_target(self):
        """Update the target-coordinate preview."""

        point = (
            self.target_point()
        )

        self.target_position.setText(
            (
                f"X {float(point.x):.3f}, "
                f"Y {float(point.y):.3f}, "
                f"Z {float(point.z):.3f} mm"
            )
        )


class CreateOffsetNodeCommand:
    """Create a ForgeCAD node relative to one selected node."""

    def GetResources(self):
        return {
            "MenuText":
                "Create Offset Node",
            "ToolTip": (
                "Create a new ForgeCAD node at an "
                "X, Y, Z offset from a selected node"
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

        if len(selection) != 1:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select One Node",
                (
                    "Select exactly one ForgeCAD node "
                    "to use as the offset origin."
                ),
            )
            return

        source_node = (
            selection[0]
        )

        if not is_forgecad_node(
            source_node
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

        dialog = OffsetNodeDialog(
            source_node,
            FreeCADGui.getMainWindow(),
        )

        if (
            dialog.exec_()
            != QtGui.QDialog.Accepted
        ):
            return

        # Resolve the requested point before opening a transaction.
        # Reusing an existing node does not modify the document and should
        # therefore not create an empty Undo/Redo history entry.
        target_point = offset_point(
            source_node.Position,
            dialog.x_offset.value(),
            dialog.y_offset.value(),
            dialog.z_offset.value(),
        )

        existing = existing_node_at_point(
            document,
            target_point,
        )

        if existing is not None:
            node_object = existing
            created = False

        else:
            transaction_started = False

            try:
                if hasattr(
                    document,
                    "openTransaction",
                ):
                    document.openTransaction(
                        "Create ForgeCAD Offset Node"
                    )

                    transaction_started = True

                node_object, created = (
                    create_offset_node(
                        document,
                        source_node,
                        dialog.x_offset.value(),
                        dialog.y_offset.value(),
                        dialog.z_offset.value(),
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
                    "Node Creation Failed",
                    str(error),
                )
                return

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.Selection.addSelection(
            node_object
        )

        if not created:
            QtGui.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "Existing Node Reused",
                (
                    f"{node_object.NodeID} already exists "
                    "at the requested position."
                ),
            )

        FreeCADGui.activeDocument().activeView().fitAll()

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Create Offset Node command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        CreateOffsetNodeCommand(),
    )
    