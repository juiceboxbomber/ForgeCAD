"""FreeCAD command for inspecting and configuring a ForgeCAD tube joint."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.commands.generate_from_selection import (
    regenerate_frame,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    frame_member_objects,
    is_forgecad_node,
    joint_from_node_object,
    node_from_freecad_object,
    structural_member_from_freecad_object,
)
from forgecad.adapters.freecad.joint_treatment_options import (
    selected_option_index,
    treatment_options_for_members,
)
from forgecad.adapters.freecad.joint_treatment_store import (
    load_joint_treatment,
    save_joint_treatment,
    vector_key,
)
from forgecad.services.joint_inspector import (
    inspect_joint,
)

from forgecad.services.joint_service import (
    member_touches_node,
)


COMMAND_NAME = "ForgeCAD_InspectJoint"


class InspectionNode:
    """
    Lightweight node representation for joint inspection.

    This allows a Joints-tree item to be inspected even when
    the project does not contain generated ForgeCAD node objects.
    """

    def __init__(
        self,
        node_id,
        position,
    ):
        self.NodeID = str(
            node_id
        )

        self.Position = (
            position
        )


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


def is_joint_status_object(
    obj,
):
    """Return True when an object is a ForgeCAD joint-status object."""

    if obj is None:
        return False

    required_properties = (
        "JointID",
        "NodeKey",
        "Position",
        "ReviewStatus",
    )

    return all(
        hasattr(
            obj,
            property_name,
        )
        for property_name
        in required_properties
    )


def node_object_at_position(
    document,
    position,
):
    """Return the ForgeCAD node located at a position."""

    if document is None:
        return None

    nodes_group = document.getObject(
        "ForgeCADNodes"
    )

    if nodes_group is None:
        return None

    target_key = point_key(
        position
    )

    for obj in nodes_group.Group:
        if not is_forgecad_node(
            obj
        ):
            continue

        if point_key(
            obj.Position
        ) == target_key:
            return obj

    return None


def node_object_for_inspection(
    document,
    selected_object,
):
    """
    Resolve an Inspect Joint selection to a node-like object.

    The user may select:

        - a generated ForgeCAD node
        - a status/marker object from the Joints group

    A physical Nodes-group object is not required. When a
    Joints-tree item is selected and no generated node exists
    at that position, ForgeCAD creates a lightweight inspection
    node using the joint marker's stored position.
    """

    if is_forgecad_node(
        selected_object
    ):
        return selected_object

    if not is_joint_status_object(
        selected_object
    ):
        return None

    existing_node = (
        node_object_at_position(
            document,
            selected_object.Position,
        )
    )

    if existing_node is not None:
        return existing_node

    joint_id = str(
        getattr(
            selected_object,
            "JointID",
            "Joint",
        )
    ).strip()

    if not joint_id:
        joint_id = "Joint"

    return InspectionNode(
        node_id=joint_id,
        position=selected_object.Position,
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
    """Return generated FreeCAD structural members connected to a node."""

    if document is None:
        return []

    if not is_forgecad_node(
        node_object
    ):
        return []

    node = node_from_freecad_object(
        node_object
    )

    connected = []

    for member_object in frame_member_objects(
        document
    ):
        member = (
            structural_member_from_freecad_object(
                member_object
            )
        )

        if member_touches_node(
            member,
            node,
        ):
            connected.append(
                member_object
            )

    return connected


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


def treatment_builder_label(
    option,
):
    """Return builder-friendly text for one joint-treatment option."""

    mode = str(
        getattr(
            getattr(
                option,
                "mode",
                "",
            ),
            "value",
            getattr(
                option,
                "mode",
                "",
            ),
        )
    ).strip()

    label = str(
        getattr(
            option,
            "label",
            "",
        )
    ).strip()

    if mode == "auto":
        return (
            "Automatic - Let ForgeCAD choose"
        )

    if mode == "member_through":
        if label.endswith(
            " Through"
        ):
            member_name = label[
                :-len(
                    " Through"
                )
            ].strip()

            return (
                f"{member_name} Through - "
                f"Keep {member_name} continuous"
            )

        return (
            f"{label} - Keep this member continuous"
        )

    if mode == "through_pair":
        if label.endswith(
            " Through Pair"
        ):
            pair_name = label[
                :-len(
                    " Through Pair"
                )
            ].strip()

            return (
                f"{pair_name} Through Pair - "
                "Keep these members continuous"
            )

        return (
            f"{label} - Keep these members continuous"
        )

    if mode in (
        "both_coped",
        "both_mitered",
    ):
        return (
            f"{label} - Miter both members at the joint"
        )

    return label


def treatment_builder_prompt():
    """Return the plain-language treatment question."""

    return "How should this joint be built?"


class JointInspectorDialog(
    QtGui.QDialog
):
    """Display and configure one ForgeCAD joint."""

    def __init__(
        self,
        document,
        node_object,
        inspection,
        member_objects,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.document = (
            document
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

        self.member_names = {}

        self.treatment_options = ()

        self.setWindowTitle(
            "ForgeCAD Joint Inspector"
        )

        self.setMinimumWidth(
            760
        )

        self.setMinimumHeight(
            600
        )

        self.build_member_name_map()

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
            "Automatic Notches:",
            QtGui.QLabel(
                str(
                    inspection.notch_count
                )
            ),
        )

        # -------------------------------------------------
        # Treatment controls
        # -------------------------------------------------

        treatment_group = (
            QtGui.QGroupBox(
                "Build This Joint"
            )
        )

        treatment_layout = (
            QtGui.QVBoxLayout()
        )

        treatment_question = (
            QtGui.QLabel(
                treatment_builder_prompt()
            )
        )

        treatment_question.setWordWrap(
            True
        )

        treatment_layout.addWidget(
            treatment_question
        )

        treatment_form = (
            QtGui.QFormLayout()
        )

        self.treatment_combo = (
            QtGui.QComboBox()
        )

        treatment_form.addRow(
            "Build choice:",
            self.treatment_combo,
        )

        treatment_layout.addLayout(
            treatment_form
        )

        self.treatment_status = (
            QtGui.QLabel()
        )

        self.treatment_status.setWordWrap(
            True
        )

        treatment_layout.addWidget(
            self.treatment_status
        )

        self.apply_treatment_button = (
            QtGui.QPushButton(
                "Apply Treatment"
            )
        )

        self.apply_treatment_button.clicked.connect(
            self.apply_treatment
        )

        treatment_layout.addWidget(
            self.apply_treatment_button
        )

        treatment_group.setLayout(
            treatment_layout
        )

        self.refresh_treatment_controls()

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
            "Automatic Notches",
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
            treatment_group
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

    def build_member_name_map(
        self,
    ):
        """Map temporary domain members to generated member names."""

        self.member_names = {}

        for (
            domain_member,
            member_object,
        ) in zip(
            self.inspection.joint.members,
            self.member_objects,
        ):
            self.member_names[
                id(domain_member)
            ] = member_display_name(
                member_object
            )

    def saved_treatment(
        self,
    ):
        """Return the treatment currently stored for this joint."""

        return load_joint_treatment(
            self.document,
            vector_key(
                self.node_object.Position
            ),
        )

    def refresh_treatment_controls(
        self,
    ):
        """Reload treatment options and select the saved treatment."""

        self.treatment_options = (
            treatment_options_for_members(
                self.member_objects
            )
        )

        saved = (
            self.saved_treatment()
        )

        current_index = (
            selected_option_index(
                self.treatment_options,
                saved,
            )
        )

        self.treatment_combo.blockSignals(
            True
        )

        self.treatment_combo.clear()

        for option in (
            self.treatment_options
        ):
            self.treatment_combo.addItem(
                treatment_builder_label(
                    option
                )
            )

        if (
            current_index >= 0
            and current_index
            < len(
                self.treatment_options
            )
        ):
            self.treatment_combo.setCurrentIndex(
                current_index
            )

        self.treatment_combo.blockSignals(
            False
        )

        if saved is None:
            self.treatment_status.setText(
                (
                    "Current build: Automatic "
                    "(ForgeCAD chooses the joint treatment)"
                )
            )
        else:
            selected_index = (
                self.treatment_combo.currentIndex()
            )

            if (
                selected_index >= 0
                and selected_index
                < len(
                    self.treatment_options
                )
            ):
                option = (
                    self.treatment_options[
                        selected_index
                    ]
                )

                self.treatment_status.setText(
                    (
                        "Current build: "
                        f"{option.label}"
                    )
                )
            else:
                self.treatment_status.setText(
                    "Current build: Automatic"
                )

    def refresh_after_regeneration(
        self,
    ):
        """
        Rebuild inspector references after frame regeneration.

        Generated frame members are replaced during regeneration,
        so the dialog must discard its old member-object references.
        """

        self.member_objects = (
            connected_member_objects(
                self.document,
                self.node_object,
            )
        )

        joint = (
            joint_from_node_object(
                self.document,
                self.node_object,
            )
        )

        self.inspection = (
            inspect_joint(
                joint
            )
        )

        self.build_member_name_map()

        self.refresh_treatment_controls()

    def apply_treatment(
        self,
    ):
        """Save the selected treatment and regenerate atomically."""

        index = (
            self.treatment_combo.currentIndex()
        )

        if (
            index < 0
            or index
            >= len(
                self.treatment_options
            )
        ):
            return

        option = (
            self.treatment_options[
                index
            ]
        )

        transaction_started = False

        try:
            transaction_supported = all(
                hasattr(
                    self.document,
                    method_name,
                )
                for method_name in (
                    "openTransaction",
                    "commitTransaction",
                    "abortTransaction",
                )
            )

            if transaction_supported:
                self.document.openTransaction(
                    "Change ForgeCAD Joint Treatment"
                )
                transaction_started = True

            save_joint_treatment(
                self.document,
                vector_key(
                    self.node_object.Position
                ),
                option.mode,
                option.through_layout_ids,
            )

            regenerate_frame(
                self.document,
                clear_selection=False,
                adjust_view=False,
            )

            self.refresh_after_regeneration()

            if transaction_started:
                self.document.commitTransaction()
                transaction_started = False

        except Exception as error:
            if transaction_started:
                try:
                    self.document.abortTransaction()
                except Exception:
                    pass

            QtGui.QMessageBox.warning(
                self,
                "Joint Treatment Failed",
                str(error),
            )
            return

        self.treatment_status.setText(
            (
                "Current treatment: "
                f"{option.label}"
            )
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

    def create_members_tab(
        self,
    ):
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

            for (
                column_index,
                value,
            ) in enumerate(
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

    def create_angles_tab(
        self,
    ):
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

            for (
                column_index,
                value,
            ) in enumerate(
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

    def create_notches_tab(
        self,
    ):
        """
        Create the automatic-notch analysis tab.

        This tab intentionally reports ForgeCAD's geometric
        automatic analysis. The Treatment control above reports
        the actual persistent designer-selected treatment.
        """

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

            for (
                column_index,
                value,
            ) in enumerate(
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
                        "identified at this joint."
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
    """
    Inspect and configure one selected ForgeCAD joint.

    The selection may be either a ForgeCAD node or a status
    object from the project's Joints group.
    """

    def GetResources(
        self,
    ):
        return {
            "MenuText":
                "Inspect Joint",
            "ToolTip": (
                "Inspect connected members, angles, "
                "and fabrication treatment at a ForgeCAD joint"
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

        if len(selection) != 1:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select One Joint",
                (
                    "Select exactly one ForgeCAD node "
                    "or Joints-tree item to inspect."
                ),
            )
            return

        selected_object = (
            selection[
                0
            ]
        )

        node_object = (
            node_object_for_inspection(
                document,
                selected_object,
            )
        )

        if node_object is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                (
                    "Select a ForgeCAD node or "
                    "a joint from the Joints group."
                ),
            )
            return

        joint = (
            joint_from_node_object(
                document,
                node_object,
            )
        )

        if (
            joint.member_count
            < 2
        ):
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

        dialog = (
            JointInspectorDialog(
                document,
                node_object,
                inspection,
                connected_objects,
                FreeCADGui.getMainWindow(),
            )
        )

        dialog.exec_()

    def IsActive(
        self,
    ):
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
    