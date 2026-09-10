"""Read-only FreeCAD inspector for a ForgeCAD tube joint."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.joint_inspector_adapter import (
    frame_member_objects,
    is_forgecad_node,
    joint_from_node_object,
    node_from_freecad_object,
    structural_member_from_freecad_object,
)
from forgecad.adapters.freecad.joint_treatment_store import (
    load_joint_cope_pairs,
    load_joint_through_pairs,
    load_joint_treatment,
    vector_key,
)
from forgecad.services.joint_inspector import inspect_joint
from forgecad.services.joint_review import fabrication_rows
from forgecad.services.joint_service import member_touches_node


COMMAND_NAME = "ForgeCAD_InspectJoint"


class InspectionNode:
    """Lightweight node-like object for a joint with no generated node object."""

    def __init__(self, node_id, position):
        self.NodeID = str(node_id)
        self.Position = position


def point_key(point, precision=6):
    return (
        round(float(point.x), precision),
        round(float(point.y), precision),
        round(float(point.z), precision),
    )


def is_joint_status_object(obj):
    if obj is None:
        return False
    return all(
        hasattr(obj, name)
        for name in ("JointID", "NodeKey", "Position", "ReviewStatus")
    )


def node_object_at_position(document, position):
    if document is None:
        return None
    group = document.getObject("ForgeCADNodes")
    if group is None:
        return None
    wanted = point_key(position)
    for obj in group.Group:
        if is_forgecad_node(obj) and point_key(obj.Position) == wanted:
            return obj
    return None


def node_object_for_inspection(document, selected_object):
    """Resolve a generated node or Joints-tree status object for review."""
    if is_forgecad_node(selected_object):
        return selected_object
    if not is_joint_status_object(selected_object):
        return None

    existing = node_object_at_position(document, selected_object.Position)
    if existing is not None:
        return existing

    joint_id = str(
        getattr(selected_object, "JointID", "Joint") or "Joint"
    ).strip() or "Joint"
    return InspectionNode(joint_id, selected_object.Position)


def connected_member_objects(document, node_object):
    """Return objects touching the node at an endpoint or interior location."""
    if document is None or not is_forgecad_node(node_object):
        return []
    node = node_from_freecad_object(node_object)
    result = []
    for obj in frame_member_objects(document):
        try:
            member = structural_member_from_freecad_object(obj)
        except (TypeError, ValueError, AttributeError):
            continue
        if member_touches_node(member, node):
            result.append(obj)
    return result


def member_display_name(member_object):
    member_id = str(getattr(member_object, "MemberID", "") or "").strip()
    member_name = str(getattr(member_object, "MemberName", "") or "").strip()
    if member_id and member_name:
        return f"{member_id} - {member_name}"
    if member_id:
        return member_id
    return str(getattr(member_object, "Label", "") or "Member").strip() or "Member"


def classification_display_name(classification):
    names = {
        "straight": "Straight",
        "corner": "Corner",
        "t_joint": "T-Joint",
        "multi_member": "Multi-Member",
        "invalid": "Invalid",
    }
    value = str(classification)
    return names.get(value, value.replace("_", " ").title())


class JointInspectorDialog(QtGui.QDialog):
    """Display one joint without changing fabrication state."""

    def __init__(self, document, node_object, inspection, member_objects, parent=None):
        super().__init__(parent)
        self.document = document
        self.node_object = node_object
        self.inspection = inspection
        self.member_objects = list(member_objects)
        self.member_names = {}
        self.names_by_layout = {}

        self.setWindowTitle("ForgeCAD Joint Inspector - Review")
        self.resize(720, 520)
        self.build_member_name_maps()

        layout = QtGui.QVBoxLayout()

        review_note = QtGui.QLabel(
            "Review only. To change fabrication, select tubes in the model and use "
            "Miter Selected, Cope Selected, Through Selected, or Clear Selected Treatment."
        )
        review_note.setWordWrap(True)
        layout.addWidget(review_note)
        layout.addSpacing(6)

        summary = QtGui.QFormLayout()
        position = node_object.Position
        summary.addRow("Node:", QtGui.QLabel(str(node_object.NodeID)))
        summary.addRow(
            "Position:",
            QtGui.QLabel(
                f"X {float(position.x):.3f}, Y {float(position.y):.3f}, "
                f"Z {float(position.z):.3f} mm"
            ),
        )
        summary.addRow(
            "Classification:",
            QtGui.QLabel(classification_display_name(inspection.classification)),
        )
        summary.addRow("Connected Members:", QtGui.QLabel(str(inspection.member_count)))
        summary.addRow("Through Members:", QtGui.QLabel(str(inspection.through_member_count)))
        summary.addRow("Branch Members:", QtGui.QLabel(str(inspection.branch_member_count)))
        layout.addLayout(summary)
        layout.addSpacing(6)

        tabs = QtGui.QTabWidget()
        tabs.addTab(self.create_fabrication_tab(), "Saved Fabrication")
        tabs.addTab(self.create_members_tab(), "Members")
        tabs.addTab(self.create_angles_tab(), "Angles")
        tabs.addTab(self.create_notches_tab(), "Automatic Analysis")
        layout.addWidget(tabs)

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(self.accept)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def build_member_name_maps(self):
        self.member_names = {}
        self.names_by_layout = {}
        for domain_member, member_object in zip(
            self.inspection.joint.members,
            self.member_objects,
        ):
            label = member_display_name(member_object)
            self.member_names[id(domain_member)] = label
            layout_id = str(getattr(member_object, "SourceLayoutID", "") or "").strip()
            if layout_id:
                self.names_by_layout[layout_id] = label

    def domain_member_name(self, member):
        return self.member_names.get(id(member), "Member")

    @staticmethod
    def configure_table(table):
        table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def _table_widget(self, headers, rows):
        widget = QtGui.QWidget()
        table = QtGui.QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(list(headers))
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                table.setItem(
                    row_index,
                    column_index,
                    QtGui.QTableWidgetItem(str(value)),
                )
        self.configure_table(table)
        box = QtGui.QVBoxLayout()
        box.addWidget(table)
        widget.setLayout(box)
        return widget

    def create_fabrication_tab(self):
        key = vector_key(self.node_object.Position)
        saved = load_joint_treatment(self.document, key)
        cope_pairs = load_joint_cope_pairs(self.document, key)
        through_pairs = load_joint_through_pairs(self.document, key)
        rows = fabrication_rows(saved, cope_pairs, through_pairs, self.names_by_layout)
        return self._table_widget(
            ("Operation", "Member", "Other / Details"),
            rows,
        )

    def create_members_tab(self):
        rows = []
        for item in self.inspection.members:
            rows.append((
                self.domain_member_name(item.member),
                item.role.title(),
                f"{item.length_mm:.2f}",
                f"{item.outside_diameter_mm:.3f}",
                f"{item.wall_thickness_mm:.3f}",
            ))
        return self._table_widget(
            ("Member", "Role", "Length (mm)", "OD (mm)", "Wall (mm)"),
            rows,
        )

    def create_angles_tab(self):
        rows = []
        for item in self.inspection.angles:
            rows.append((
                self.domain_member_name(item.first_member),
                self.domain_member_name(item.second_member),
                f"{item.angle_degrees:.2f}",
            ))
        return self._table_widget(("First Member", "Second Member", "Angle (deg)"), rows)

    def create_notches_tab(self):
        rows = []
        for item in self.inspection.notches:
            rows.append((
                self.domain_member_name(item.branch_member),
                item.branch_end.title(),
                f"{item.angle_degrees:.2f}",
                f"{item.branch_outside_diameter_mm:.3f}",
                f"{item.through_outside_diameter_mm:.3f}",
            ))
        return self._table_widget(
            ("Branch", "End", "Angle (deg)", "Branch OD (mm)", "Target OD (mm)"),
            rows,
        )


class InspectJointCommand:
    """Review one selected ForgeCAD joint."""

    def GetResources(self):
        return {
            "MenuText": "Inspect Joint",
            "ToolTip": (
                "Review connected members, angles, automatic analysis, "
                "and saved fabrication operations at a ForgeCAD joint"
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

        selection = list(FreeCADGui.Selection.getSelection())
        if len(selection) != 1:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select One Joint",
                "Select exactly one ForgeCAD node or Joints-tree item to inspect.",
            )
            return

        node_object = node_object_for_inspection(document, selection[0])
        if node_object is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                "Select a ForgeCAD node or a joint from the Joints group.",
            )
            return

        joint = joint_from_node_object(document, node_object)
        if joint.member_count < 2:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Joint At Node",
                f"{node_object.NodeID} has fewer than two connected frame members.",
            )
            return

        try:
            inspection = inspect_joint(joint)
        except ValueError as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Joint Analysis Failed",
                str(error),
            )
            return

        dialog = JointInspectorDialog(
            document,
            node_object,
            inspection,
            connected_member_objects(document, node_object),
            FreeCADGui.getMainWindow(),
        )
        dialog.exec_()

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


def register_command():
    FreeCADGui.addCommand(COMMAND_NAME, InspectJointCommand())
