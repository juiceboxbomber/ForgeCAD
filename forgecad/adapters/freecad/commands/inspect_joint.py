"""FreeCAD command for inspecting a ForgeCAD tube joint."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.joint_inspector_adapter import (
    frame_member_objects,
    is_forgecad_node,
    joint_from_node_object,
)
from forgecad.services.joint_inspector import (
    inspect_joint,
)


COMMAND_NAME = "ForgeCAD_InspectJoint"


def point_key(
    point,
    precision=6,
):
    """Return a stable XYZ key for a FreeCAD-like point."""

    return (
        round(
            float(point.x),
            precision,
        ),
        round(
            float(point.y),
            precision,
        ),
        round(
            float(point.z),
            precision,
        ),
    )


def member_object_touches_position(
    member_object,
    position,
):
    """Return True when a generated member touches a position."""

    target = point_key(
        position
    )

    for endpoint in (
        member_object.StartPoint,
        member_object.EndPoint,
    ):
        if point_key(
            endpoint
        ) == target:
            return True

    return False


def connected_member_objects(
    document,
    node_object,
):
    """Return generated FreeCAD members connected to a node."""

    if document is None:
        return []

    if not is_forgecad_node(
        node_object
    ):
        return []

    return [
        member_object
        for member_object
        in frame_member_objects(
            document
        )
        if member_object_touches_position(
            member_object,
            node_object.Position,
        )
    ]


def member_display_name(
    member_object,
):
    """Return a readable generated-member name."""

    member_id = str(
        getattr(
            member_object,
            "MemberID",
            "",
        )
    ).strip()

    member_name = str(
        getattr(
            member_object,
            "MemberName",
            "",
        )
    ).strip()

    if member_id and member_name:
        return (
            f"{member_id} - "
            f"{member_name}"
        )

    if member_id:
        return member_id

    return "Member"


def classification_display_name(
    classification,
):
    """Return a human-readable joint classification."""

    names = {
        "straight": "Straight",
        "corner": "Corner",
        "t_joint": "T-Joint",
        "multi_member": "Multi-Member",
        "invalid": "Invalid",
    }

    return names.get(
        str(classification),
        str(classification)
        .replace(
            "_",
            " ",
        )
        .title(),
    )


class JointInspectorDialog(
    QtGui.QDialog
):
    """Display analysis information for one ForgeCAD joint."""

    def __init__(
        self,
        node_object,
        inspection,
        member_objects,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.node_object = (
            node_object
        )

        self.inspection = (
            inspection
        )

        self.member_objects = list(
            member_objects
        )

        self.setWindowTitle(
            "ForgeCAD Joint Inspector"
        )

        self.setMinimumWidth(
            720
        )

        self.setMinimumHeight(
            520
        )

        # -------------------------------------------------
        # Map temporary domain members back to generated
        # FreeCAD member labels.
        # -------------------------------------------------

        self.member_names = {}

        for domain_member, member_object in zip(
            inspection.joint.members,
            self.member_objects,
        ):
            self.member_names[
                id(domain_member)
            ] = member_display_name(
                member_object
            )

        # -------------------------------------------------
        # Joint summary
        # -------------------------------------------------

        summary_form = (
            QtGui.QFormLayout()
        )

        node_id = str(
            node_object.NodeID
        )

        position = (
            node_object.Position
        )

        summary_form.addRow(
            "Node:",
            QtGui.QLabel(
                node_id
            ),
        )

        summary_form.addRow(
            "Position:",
            QtGui.QLabel(
                (
                    f"X {float(position.x):.3f}, "
                    f"Y {float(position.y):.3f}, "
                    f"Z {float(position.z):.3f} mm"
                )
            ),
        )

        summary_form.addRow(
            "Classification:",
            QtGui.QLabel(
                classification_display_name(
                    inspection.classification
                )
            ),
        )

        summary_form.addRow(
            "Connected Members:",
            QtGui.QLabel(
                str(
                    inspection.member_count
                )
            ),
        )

        summary_form.addRow(
            "Through Members:",
            QtGui.QLabel(
                str(
                    inspection.through_member_count
                )
            ),
        )

        summary_form.addRow(
            "Branch Members:",
            QtGui.QLabel(
                str(
                    inspection.branch_member_count
                )
            ),
        )

        summary_form.addRow(
            "Required Notches:",
            QtGui.QLabel(
                str(
                    inspection.notch_count
                )
            ),
        )

        # -------------------------------------------------
        # Tabs
        # -------------------------------------------------

        tabs = (
            QtGui.QTabWidget()
        )

        tabs.addTab(
            self.create_members_tab(),
            "Members",
        )

        tabs.addTab(
            self.create_angles_tab(),
            "Angles",
        )

        tabs.addTab(
            self.create_notches_tab(),
            "Notches",
        )

        # -------------------------------------------------
        # Close button
        # -------------------------------------------------

        buttons = (
            QtGui.QDialogButtonBox(
                QtGui.QDialogButtonBox.Close
            )
        )

        buttons.rejected.connect(
            self.reject
        )

        buttons.clicked.connect(
            self.accept
        )

        # -------------------------------------------------
        # Main layout
        # -------------------------------------------------

        layout = (
            QtGui.QVBoxLayout()
        )

        layout.addLayout(
            summary_form
        )

        layout.addSpacing(
            8
        )

        layout.addWidget(
            tabs
        )

        layout.addSpacing(
            8
        )

        layout.addWidget(
            buttons
        )

        self.setLayout(
            layout
        )

    def domain_member_name(
        self,
        member,
    ):
        """Return display name for a temporary domain member."""

        return self.member_names.get(
            id(member),
            "Member",
        )

    @staticmethod
    def configure_table(
        table,
    ):
        """Apply common read-only table behavior."""

        table.setEditTriggers(
            QtGui.QAbstractItemView.NoEditTriggers
        )

        table.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows
        )

        table.resizeColumnsToContents()

        header = (
            table.horizontalHeader()
        )

        header.setStretchLastSection(
            True
        )

    def create_members_tab(self):
        """Create connected-member information tab."""

        widget = (
            QtGui.QWidget()
        )

        table = (
            QtGui.QTableWidget()
        )

        table.setColumnCount(
            5
        )

        table.setHorizontalHeaderLabels(
            [
                "Member",
                "Role",
                "Length (mm)",
                "OD (mm)",
                "Wall (mm)",
            ]
        )

        table.setRowCount(
            len(
                self.inspection.members
            )
        )

        for row_index, item in enumerate(
            self.inspection.members
        ):
            values = [
                self.domain_member_name(
                    item.member
                ),
                item.role.title(),
                f"{item.length_mm:.2f}",
                (
                    f"{item.outside_diameter_mm:.3f}"
                ),
                (
                    f"{item.wall_thickness_mm:.3f}"
                ),
            ]

            for column_index, value in enumerate(
                values
            ):
                table.setItem(
                    row_index,
                    column_index,
                    QtGui.QTableWidgetItem(
                        value
                    ),
                )

        self.configure_table(
            table
        )

        layout = (
            QtGui.QVBoxLayout()
        )

        layout.addWidget(
            table
        )

        widget.setLayout(
            layout
        )

        return widget

    def create_angles_tab(self):
        """Create member-pair angle tab."""

        widget = (
            QtGui.QWidget()
        )

        table = (
            QtGui.QTableWidget()
        )

        table.setColumnCount(
            3
        )

        table.setHorizontalHeaderLabels(
            [
                "First Member",
                "Second Member",
                "Angle (deg)",
            ]
        )

        table.setRowCount(
            len(
                self.inspection.angles
            )
        )

        for row_index, item in enumerate(
            self.inspection.angles
        ):
            values = [
                self.domain_member_name(
                    item.first_member
                ),
                self.domain_member_name(
                    item.second_member
                ),
                f"{item.angle_degrees:.2f}",
            ]

            for column_index, value in enumerate(
                values
            ):
                table.setItem(
                    row_index,
                    column_index,
                    QtGui.QTableWidgetItem(
                        value
                    ),
                )

        self.configure_table(
            table
        )

        layout = (
            QtGui.QVBoxLayout()
        )

        layout.addWidget(
            table
        )

        widget.setLayout(
            layout
        )

        return widget

    def create_notches_tab(self):
        """Create required-notch information tab."""

        widget = (
            QtGui.QWidget()
        )

        table = (
            QtGui.QTableWidget()
        )

        table.setColumnCount(
            5
        )

        table.setHorizontalHeaderLabels(
            [
                "Branch",
                "End",
                "Angle (deg)",
                "Branch OD (mm)",
                "Target OD (mm)",
            ]
        )

        table.setRowCount(
            len(
                self.inspection.notches
            )
        )

        for row_index, item in enumerate(
            self.inspection.notches
        ):
            values = [
                self.domain_member_name(
                    item.branch_member
                ),
                item.branch_end.title(),
                f"{item.angle_degrees:.2f}",
                (
                    f"{item.branch_outside_diameter_mm:.3f}"
                ),
                (
                    f"{item.through_outside_diameter_mm:.3f}"
                ),
            ]

            for column_index, value in enumerate(
                values
            ):
                table.setItem(
                    row_index,
                    column_index,
                    QtGui.QTableWidgetItem(
                        value
                    ),
                )

        self.configure_table(
            table
        )

        layout = (
            QtGui.QVBoxLayout()
        )

        if not self.inspection.notches:
            layout.addWidget(
                QtGui.QLabel(
                    (
                        "No automatic tube notches are "
                        "required at this joint."
                    )
                )
            )

        layout.addWidget(
            table
        )

        widget.setLayout(
            layout
        )

        return widget


class InspectJointCommand:
    """Inspect the tube joint at one selected ForgeCAD node."""

    def GetResources(self):
        return {
            "MenuText":
                "Inspect Joint",
            "ToolTip": (
                "Inspect connected members, angles, roles, "
                "and notch requirements at a ForgeCAD node"
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
                    "to inspect."
                ),
            )
            return

        node_object = (
            selection[0]
        )

        if not is_forgecad_node(
            node_object
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

        joint = (
            joint_from_node_object(
                document,
                node_object,
            )
        )

        if joint.member_count < 2:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Joint At Node",
                (
                    f"{node_object.NodeID} has fewer than "
                    "two connected frame members."
                ),
            )
            return

        try:
            inspection = (
                inspect_joint(
                    joint
                )
            )

        except ValueError as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Joint Analysis Failed",
                str(error),
            )
            return

        connected_objects = (
            connected_member_objects(
                document,
                node_object,
            )
        )

        dialog = JointInspectorDialog(
            node_object,
            inspection,
            connected_objects,
            FreeCADGui.getMainWindow(),
        )

        dialog.exec_()

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Inspect Joint command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        InspectJointCommand(),
    )
    