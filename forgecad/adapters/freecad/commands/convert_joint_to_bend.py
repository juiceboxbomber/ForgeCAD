"""FreeCAD command for converting one simple straight joint into a bend."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.bent_tube_object import (
    create_bent_tube_object,
    ensure_bent_tube_node_links,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)
from forgecad.adapters.freecad.fabrication_refresh import (
    refresh_fabrication_for_document,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    frame_member_objects,
    is_forgecad_member,
    structural_member_from_freecad_object,
)
from forgecad.adapters.freecad.joint_status_adapter import (
    joint_review_for_document,
)
from forgecad.adapters.freecad.member_removal import (
    layout_object_for_id,
)
from forgecad.adapters.freecad.topology_refresh import (
    refresh_joint_topology,
)
from forgecad.services.joint_bend import (
    bend_specification_from_joint,
)


COMMAND_NAME = "ForgeCAD_ConvertJointToBend"


def is_joint_marker(
    obj,
):
    """Return True when an object is a ForgeCAD joint-status marker."""

    if obj is None:
        return False

    return (
        hasattr(
            obj,
            "JointID",
        )
        and hasattr(
            obj,
            "NodeKey",
        )
        and hasattr(
            obj,
            "Position",
        )
    )


def selected_joint_marker():
    """Return exactly one selected ForgeCAD joint marker or None."""

    selection = list(
        FreeCADGui.Selection.getSelection()
    )

    if len(
        selection
    ) != 1:
        return None

    marker = selection[
        0
    ]

    if not is_joint_marker(
        marker
    ):
        return None

    return marker


def joint_status_for_marker(
    document,
    marker,
):
    """Resolve one disposable joint marker back to current joint review data."""

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if not is_joint_marker(
        marker
    ):
        raise ValueError(
            "Select one ForgeCAD joint sphere."
        )

    requested_key = str(
        marker.NodeKey
    ).strip()

    if not requested_key:
        raise ValueError(
            "The selected joint marker has no node key."
        )

    review = joint_review_for_document(
        document
    )

    for item in review.joints:
        if (
            str(
                item.node_key
            ).strip()
            == requested_key
        ):
            return item

    raise ValueError(
        "The selected joint no longer exists in the current frame topology."
    )


def freecad_members_for_joint(
    document,
    joint,
):
    """
    Return the exact straight FreeCAD member objects represented by a joint.

    v1 intentionally supports only two straight members. Bent members and
    multi-member joints remain untouched.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if not joint.is_simple:
        raise ValueError(
            "Convert Joint to Bend requires exactly two members."
        )

    remaining = list(
        joint.members
    )

    matches = []

    for obj in frame_member_objects(
        document
    ):
        if not is_forgecad_member(
            obj
        ):
            continue

        domain_member = (
            structural_member_from_freecad_object(
                obj
            )
        )

        for index, requested_member in enumerate(
            remaining
        ):
            if domain_member == requested_member:
                matches.append(
                    obj
                )

                del remaining[
                    index
                ]

                break

    if remaining or len(
        matches
    ) != 2:
        raise ValueError(
            "ForgeCAD could not map the joint to exactly two straight members."
        )

    return tuple(
        matches
    )


def outer_node_object(
    member_object,
    joint_node,
):
    """Return the linked endpoint node opposite the theoretical joint."""

    start_node = getattr(
        member_object,
        "StartNode",
        None,
    )

    end_node = getattr(
        member_object,
        "EndNode",
        None,
    )

    if (
        start_node is None
        or end_node is None
    ):
        raise ValueError(
            "Both straight members must have persistent endpoint-node links."
        )

    tolerance = 1e-6

    def node_matches(
        node_object,
    ):
        position = getattr(
            node_object,
            "Position",
            None,
        )

        if position is None:
            return False

        return (
            abs(
                float(
                    position.x
                )
                - float(
                    joint_node.x
                )
            )
            <= tolerance
            and abs(
                float(
                    position.y
                )
                - float(
                    joint_node.y
                )
            )
            <= tolerance
            and abs(
                float(
                    position.z
                )
                - float(
                    joint_node.z
                )
            )
            <= tolerance
        )

    if node_matches(
        start_node
    ):
        return end_node

    if node_matches(
        end_node
    ):
        return start_node

    raise ValueError(
        "A selected member is not linked to the joint node."
    )


def source_layout_objects(
    document,
    member_objects,
):
    """Return unique source-layout objects for the converted straight members."""

    layouts = []

    for member_object in member_objects:
        layout_id = str(
            getattr(
                member_object,
                "SourceLayoutID",
                "",
            )
        ).strip()

        if not layout_id:
            continue

        layout_object = layout_object_for_id(
            document,
            layout_id,
        )

        if (
            layout_object is not None
            and layout_object not in layouts
        ):
            layouts.append(
                layout_object
            )

    return tuple(
        layouts
    )


def joint_node_object(
    document,
    joint_node,
    tolerance=1e-6,
):
    """Return the persistent ForgeCAD node at the theoretical joint point."""

    if document is None:
        return None

    tree = initialize_project_tree(
        document
    )

    nodes_group = tree[
        "Nodes"
    ]

    for node_object in getattr(
        nodes_group,
        "Group",
        (),
    ):
        position = getattr(
            node_object,
            "Position",
            None,
        )

        if position is None:
            continue

        if (
            abs(
                float(
                    position.x
                )
                - float(
                    joint_node.x
                )
            )
            <= tolerance
            and abs(
                float(
                    position.y
                )
                - float(
                    joint_node.y
                )
            )
            <= tolerance
            and abs(
                float(
                    position.z
                )
                - float(
                    joint_node.z
                )
            )
            <= tolerance
        ):
            return node_object

    return None


def hide_design_geometry_for_bend(
    document,
    member_objects,
    joint_node,
):
    """
    Hide the superseded straight-layout corner after bend conversion.

    The layout objects and theoretical joint node remain persistent for
    design intent, future editing, and Undo/Redo, but they no longer clutter
    the physical bent-tube display.
    """

    layouts = source_layout_objects(
        document,
        member_objects,
    )

    for layout_object in layouts:
        view = getattr(
            layout_object,
            "ViewObject",
            None,
        )

        if view is None:
            continue

        try:
            view.Visibility = False
        except Exception:
            pass

    design_node = joint_node_object(
        document,
        joint_node,
    )

    if design_node is not None:
        view = getattr(
            design_node,
            "ViewObject",
            None,
        )

        if view is not None:
            try:
                view.Visibility = False
            except Exception:
                pass

    return (
        layouts,
        design_node,
    )


def store_bend_design_references(
    bent_object,
    layout_objects,
    design_node,
):
    """Store hidden source-layout and design-joint references on the bend."""

    if bent_object is None:
        return None

    if not hasattr(
        bent_object,
        "DesignJointNode",
    ):
        bent_object.addProperty(
            "App::PropertyLink",
            "DesignJointNode",
            "ForgeCAD Bend",
        )

    if not hasattr(
        bent_object,
        "SourceLayoutLines",
    ):
        bent_object.addProperty(
            "App::PropertyLinkList",
            "SourceLayoutLines",
            "ForgeCAD Bend",
        )

    bent_object.DesignJointNode = (
        design_node
    )

    bent_object.SourceLayoutLines = list(
        layout_objects
    )

    for property_name in (
        "DesignJointNode",
        "SourceLayoutLines",
    ):
        try:
            bent_object.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return bent_object


def remove_straight_member_object(
    document,
    member_object,
):
    """
    Remove one straight member while preserving its source layout object.

    Bend conversion hides the source layout separately so the theoretical
    design geometry remains available without cluttering the physical view.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if member_object is None:
        raise ValueError(
            "A straight member object is required."
        )

    frame_group = document.getObject(
        "ForgeCADFrame"
    )

    if frame_group is not None:
        try:
            frame_group.removeObject(
                member_object
            )
        except Exception:
            pass

    object_name = str(
        getattr(
            member_object,
            "Name",
            "",
        )
    ).strip()

    if not object_name:
        raise ValueError(
            "ForgeCAD member has no document object name."
        )

    document.removeObject(
        object_name
    )


def create_bent_tube_from_joint(
    document,
    joint_status,
    centerline_radius_mm,
):
    """
    Replace one simple two-member corner with one persistent bent tube.

    The source layout and theoretical corner node remain stored as hidden
    design references. The physical bent tube links the two outer endpoint
    nodes and becomes the visible structural result.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    joint = joint_status.joint

    member_objects = freecad_members_for_joint(
        document,
        joint,
    )

    specification = bend_specification_from_joint(
        joint,
        centerline_radius_mm=centerline_radius_mm,
        name=f"Bend {joint_status.node_key}",
    )

    first_outer_node = outer_node_object(
        member_objects[
            0
        ],
        joint.node,
    )

    second_outer_node = outer_node_object(
        member_objects[
            1
        ],
        joint.node,
    )

    layout_objects = source_layout_objects(
        document,
        member_objects,
    )

    design_node = joint_node_object(
        document,
        joint.node,
    )

    bent_object = create_bent_tube_object(
        document,
        specification.tube,
    )

    bent_object.TubeName = (
        f"Bend {joint_status.node_key}"
    )

    bent_object.StartPoint = FreeCAD.Vector(
        float(
            specification.start_node.x
        ),
        float(
            specification.start_node.y
        ),
        float(
            specification.start_node.z
        ),
    )

    bent_object.InitialDirection = FreeCAD.Vector(
        float(
            specification.initial_direction.x
        ),
        float(
            specification.initial_direction.y
        ),
        float(
            specification.initial_direction.z
        ),
    )

    bent_object.InitialBendNormal = FreeCAD.Vector(
        float(
            specification.bend_normal.x
        ),
        float(
            specification.bend_normal.y
        ),
        float(
            specification.bend_normal.z
        ),
    )

    ensure_bent_tube_node_links(
        bent_object,
        first_outer_node,
        second_outer_node,
    )

    store_bend_design_references(
        bent_object,
        layout_objects,
        design_node,
    )

    tree = initialize_project_tree(
        document
    )

    tree[
        "Bent Tubes"
    ].addObject(
        bent_object
    )

    bent_object.Proxy.update_shape(
        bent_object
    )

    for member_object in member_objects:
        remove_straight_member_object(
            document,
            member_object,
        )

    hide_design_geometry_for_bend(
        document,
        member_objects,
        joint.node,
    )

    document.recompute()

    refresh_joint_topology(
        document
    )

    refresh_fabrication_for_document(
        document
    )

    document.recompute()

    return bent_object


def begin_convert_joint_to_bend_transaction(
    document,
):
    """Open one Undo transaction for the complete joint-to-bend conversion."""

    if (
        document is None
        or not hasattr(
            document,
            "openTransaction",
        )
    ):
        return False

    document.openTransaction(
        "Convert ForgeCAD Joint to Bend"
    )

    return True


def finish_convert_joint_to_bend_transaction(
    document,
    transaction_started,
):
    """Commit a successful joint-to-bend conversion."""

    if (
        transaction_started
        and hasattr(
            document,
            "commitTransaction",
        )
    ):
        document.commitTransaction()


def abort_convert_joint_to_bend_transaction(
    document,
    transaction_started,
):
    """Abort a failed joint-to-bend conversion."""

    if (
        not transaction_started
        or not hasattr(
            document,
            "abortTransaction",
        )
    ):
        return

    try:
        document.abortTransaction()
    except Exception:
        pass


class ConvertJointToBendDialog(
    QtGui.QDialog
):
    """Collect the bend centerline radius for one selected joint."""

    def __init__(
        self,
        joint_id,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.setWindowTitle(
            "Convert Joint to Bend"
        )

        self.setMinimumWidth(
            360
        )

        joint_label = QtGui.QLabel(
            (
                f"Convert {joint_id} from two straight members "
                "into one continuous bent tube."
            )
        )

        joint_label.setWordWrap(
            True
        )

        self.radius_box = (
            QtGui.QDoubleSpinBox()
        )

        self.radius_box.setRange(
            0.001,
            1_000_000.0,
        )

        self.radius_box.setDecimals(
            3
        )

        self.radius_box.setSingleStep(
            25.0
        )

        self.radius_box.setValue(
            100.0
        )

        form = QtGui.QFormLayout()

        form.addRow(
            "Centerline Radius (mm):",
            self.radius_box,
        )

        note = QtGui.QLabel(
            (
                "The original layout corner remains stored as the theoretical "
                "design intersection, but its source layout lines and corner "
                "node are hidden after the physical bend is created."
            )
        )

        note.setWordWrap(
            True
        )

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok
            | QtGui.QDialogButtonBox.Cancel
        )

        buttons.button(
            QtGui.QDialogButtonBox.Ok
        ).setText(
            "Create Bend"
        )

        buttons.accepted.connect(
            self.accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout = QtGui.QVBoxLayout()

        layout.addWidget(
            joint_label
        )

        layout.addLayout(
            form
        )

        layout.addWidget(
            note
        )

        layout.addWidget(
            buttons
        )

        self.setLayout(
            layout
        )

        self.radius_box.setFocus()


class ConvertJointToBendCommand:
    """Convert one selected simple joint into a continuous bent tube."""

    def GetResources(
        self,
    ):
        return {
            "MenuText":
                "Convert Joint to Bend",
            "ToolTip": (
                "Replace a two-straight-member joint with "
                "one continuous bent tube"
            ),
        }

    def Activated(
        self,
    ):
        document = FreeCAD.ActiveDocument

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Document",
                "Open or create a ForgeCAD project first.",
            )
            return

        marker = selected_joint_marker()

        if marker is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select One Joint",
                (
                    "Select exactly one ForgeCAD joint sphere, "
                    "then run Convert Joint to Bend."
                ),
            )
            return

        try:
            joint_status = joint_status_for_marker(
                document,
                marker,
            )

            if not joint_status.joint.is_simple:
                raise ValueError(
                    "Convert Joint to Bend requires exactly two members."
                )

            freecad_members_for_joint(
                document,
                joint_status.joint,
            )

        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Cannot Convert Joint",
                str(
                    error
                ),
            )
            return

        dialog = ConvertJointToBendDialog(
            str(
                marker.JointID
            ),
            FreeCADGui.getMainWindow(),
        )

        if (
            dialog.exec_()
            != QtGui.QDialog.Accepted
        ):
            return

        transaction_started = False

        try:
            transaction_started = (
                begin_convert_joint_to_bend_transaction(
                    document
                )
            )

            bent_object = (
                create_bent_tube_from_joint(
                    document,
                    joint_status,
                    dialog.radius_box.value(),
                )
            )

            finish_convert_joint_to_bend_transaction(
                document,
                transaction_started,
            )

        except (
            ValueError,
            TypeError,
            RuntimeError,
            KeyError,
            AttributeError,
        ) as error:
            abort_convert_joint_to_bend_transaction(
                document,
                transaction_started,
            )

            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Convert Joint to Bend Failed",
                str(
                    error
                ),
            )
            return

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.Selection.addSelection(
            bent_object
        )

        try:
            FreeCADGui.activeDocument().activeView().fitAll()
        except Exception:
            pass

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Convert Joint to Bend command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        ConvertJointToBendCommand(),
    )
