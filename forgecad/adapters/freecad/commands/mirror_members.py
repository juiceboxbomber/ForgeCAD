"""Interactive FreeCAD command for mirroring ForgeCAD members."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.fabrication import (
    Node,
)
from forgecad.geometry import (
    Point3D,
)
from forgecad.adapters.freecad.commands.create_member_between_nodes import (
    create_member_between_nodes,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    structural_member_from_freecad_object,
)
from forgecad.services.member_mirror import (
    mirror_member_across_centerline,
    mirror_member_across_plane,
)
from forgecad.services.joint_treatment_mirror import (
    mirrored_treatment_data,
    mirror_node_key_across_centerline,
    mirror_node_key_across_plane,
    node_from_key,
)
from forgecad.adapters.freecad.joint_treatment_store import (
    decode_layout_ids,
    save_joint_treatment,
    treatment_objects,
)
from forgecad.adapters.freecad.topology_refresh import (
    refresh_joint_topology,
)
from forgecad.adapters.freecad.fabrication_refresh import (
    refresh_fabrication_for_document,
)
from forgecad.adapters.freecad.reference_plane_store import (
    is_reference_plane_object,
    reference_plane_from_object,
)


COMMAND_NAME = "ForgeCAD_MirrorMembers"

_active_tool = None


def is_forgecad_member(
    obj,
):
    """Return True when an object is a generated ForgeCAD straight member."""

    if obj is None:
        return False

    return all(
        hasattr(
            obj,
            property_name,
        )
        for property_name in (
            "MemberID",
            "StartPoint",
            "EndPoint",
        )
    )


def is_centerline_reference(
    obj,
):
    """Return True when an object can define a straight mirror centerline."""

    if obj is None:
        return False

    return (
        hasattr(
            obj,
            "StartPoint",
        )
        and hasattr(
            obj,
            "EndPoint",
        )
    )


def node_from_vector(
    vector,
):
    """Return a domain Node from a FreeCAD-like vector."""

    return Node(
        float(
            vector.x
        ),
        float(
            vector.y
        ),
        float(
            vector.z
        ),
    )


def point3d_from_node(
    node,
):
    """Return a Point3D from a domain Node-like object."""

    return Point3D(
        float(
            node.x
        ),
        float(
            node.y
        ),
        float(
            node.z
        ),
    )


def centerline_nodes_from_object(
    obj,
):
    """Return the two domain nodes defining a mirror reference object."""

    if not is_centerline_reference(
        obj
    ):
        raise ValueError(
            "Select one straight ForgeCAD member or layout line "
            "to use as the mirror centerline."
        )

    start = node_from_vector(
        obj.StartPoint
    )

    end = node_from_vector(
        obj.EndPoint
    )

    if (
        start.x == end.x
        and start.y == end.y
    ):
        raise ValueError(
            "Mirror centerline must have non-zero length in the XY plane."
        )

    return (
        start,
        end,
    )


def object_layout_id(
    obj,
):
    """Return a persistent layout ID from a member or layout object."""

    for property_name in (
        "SourceLayoutID",
        "LayoutID",
    ):
        value = str(
            getattr(
                obj,
                property_name,
                "",
            )
        ).strip()

        if value:
            return value

    return ""


def ensure_mirrored_source_layout_id(
    rendered_object,
    layout_object,
):
    """Ensure a mirrored member exposes its new source layout ID."""

    if rendered_object is None:
        return ""

    existing = object_layout_id(
        rendered_object
    )

    if existing:
        return existing

    layout_id = object_layout_id(
        layout_object
    )

    if (
        layout_id
        and hasattr(
            rendered_object,
            "SourceLayoutID",
        )
    ):
        try:
            rendered_object.SourceLayoutID = (
                layout_id
            )
        except Exception:
            pass

    return layout_id


def point_lies_on_member(
    point,
    member_object,
    tolerance=1e-5,
):
    """Return True when a joint point lies on a member centerline."""

    if (
        not hasattr(
            member_object,
            "StartPoint",
        )
        or not hasattr(
            member_object,
            "EndPoint",
        )
    ):
        return False

    start = member_object.StartPoint
    end = member_object.EndPoint

    ax = float(
        start.x
    )
    ay = float(
        start.y
    )
    az = float(
        start.z
    )

    bx = float(
        end.x
    )
    by = float(
        end.y
    )
    bz = float(
        end.z
    )

    px = float(
        point.x
    )
    py = float(
        point.y
    )
    pz = float(
        point.z
    )

    dx = bx - ax
    dy = by - ay
    dz = bz - az

    length_squared = (
        dx * dx
        + dy * dy
        + dz * dz
    )

    if length_squared <= (
        tolerance
        * tolerance
    ):
        return False

    projection = (
        (
            (px - ax) * dx
            + (py - ay) * dy
            + (pz - az) * dz
        )
        / length_squared
    )

    if (
        projection < -tolerance
        or projection > 1.0 + tolerance
    ):
        return False

    nearest_x = (
        ax
        + projection * dx
    )
    nearest_y = (
        ay
        + projection * dy
    )
    nearest_z = (
        az
        + projection * dz
    )

    distance_squared = (
        (px - nearest_x) ** 2
        + (py - nearest_y) ** 2
        + (pz - nearest_z) ** 2
    )

    return distance_squared <= (
        tolerance
        * tolerance
    )


def treatment_belongs_to_selected_topology(
    treatment_object,
    member_objects,
):
    """
    Return True when at least two selected members meet at a treatment.

    This prevents copying a saved decision when the other side of that
    source joint was not included in the mirror operation.
    """

    try:
        point = node_from_key(
            treatment_object.NodeKey
        )
    except (
        AttributeError,
        ValueError,
    ):
        return False

    touching_count = sum(
        1
        for member_object in member_objects
        if point_lies_on_member(
            point,
            member_object,
        )
    )

    return touching_count >= 2


def source_treatment_snapshots(
    document,
    member_objects,
):
    """Capture saved treatments belonging to selected source topology."""

    if (
        document is None
        or not hasattr(
            document,
            "getObject",
        )
    ):
        return ()

    snapshots = []

    for treatment_object in treatment_objects(
        document
    ):
        if not treatment_belongs_to_selected_topology(
            treatment_object,
            member_objects,
        ):
            continue

        snapshots.append(
            (
                str(
                    treatment_object.NodeKey
                ).strip(),
                str(
                    treatment_object.TreatmentMode
                ).strip(),
                decode_layout_ids(
                    treatment_object.ThroughLayoutIDs
                ),
            )
        )

    return tuple(
        snapshots
    )


def mirrored_layout_id_map(
    source_objects,
    mirrored_objects,
):
    """Return source layout IDs mapped to mirrored layout IDs."""

    mapping = {}

    for source_object, mirrored_object in zip(
        source_objects,
        mirrored_objects,
    ):
        source_layout_id = object_layout_id(
            source_object
        )

        mirrored_layout_id = object_layout_id(
            mirrored_object
        )

        if (
            source_layout_id
            and mirrored_layout_id
        ):
            mapping[
                source_layout_id
            ] = mirrored_layout_id

    return mapping


def save_mirrored_treatments(
    document,
    treatment_snapshots,
    layout_id_map,
    node_key_transform,
):
    """Save mirrored copies of eligible persistent joint treatments."""

    saved = []

    for (
        source_node_key,
        mode,
        through_layout_ids,
    ) in treatment_snapshots:
        treatment_data = (
            mirrored_treatment_data(
                mode,
                through_layout_ids,
                layout_id_map,
            )
        )

        if treatment_data is None:
            continue

        mirrored_mode, mirrored_layout_ids = (
            treatment_data
        )

        mirrored_node_key = (
            node_key_transform(
                source_node_key
            )
        )

        saved.append(
            save_joint_treatment(
                document,
                mirrored_node_key,
                mirrored_mode,
                mirrored_layout_ids,
            )
        )

    if saved:
        refresh_joint_topology(
            document
        )

        refresh_fabrication_for_document(
            document
        )

    return tuple(
        saved
    )


def preserve_centerline_mirrored_treatments(
    document,
    source_objects,
    mirrored_objects,
    treatment_snapshots,
    center_start,
    center_end,
):
    """Mirror saved joint decisions across the chosen centerline."""

    layout_id_map = (
        mirrored_layout_id_map(
            source_objects,
            mirrored_objects,
        )
    )

    return save_mirrored_treatments(
        document,
        treatment_snapshots,
        layout_id_map,
        lambda source_node_key: (
            mirror_node_key_across_centerline(
                source_node_key,
                center_start,
                center_end,
            )
        ),
    )


def preserve_plane_mirrored_treatments(
    document,
    source_objects,
    mirrored_objects,
    treatment_snapshots,
    plane,
    offset=0.0,
):
    """Mirror saved joint decisions across an axis-aligned plane."""

    layout_id_map = (
        mirrored_layout_id_map(
            source_objects,
            mirrored_objects,
        )
    )

    return save_mirrored_treatments(
        document,
        treatment_snapshots,
        layout_id_map,
        lambda source_node_key: (
            mirror_node_key_across_plane(
                source_node_key,
                plane,
                offset=offset,
            )
        ),
    )


def mirror_member_object(
    document,
    member_object,
    center_start,
    center_end,
):
    """Mirror one straight ForgeCAD member across the chosen centerline."""

    source_member = (
        structural_member_from_freecad_object(
            member_object
        )
    )

    mirrored_member = (
        mirror_member_across_centerline(
            source_member,
            center_start,
            center_end,
        )
    )

    # Import lazily so the command remains lightweight and testable outside
    # the FreeCAD GUI runtime.
    from forgecad.adapters.freecad.commands.draw_member_interactive import (
        get_or_create_node,
    )

    start_node = get_or_create_node(
        document,
        point3d_from_node(
            mirrored_member.start
        ),
    )

    end_node = get_or_create_node(
        document,
        point3d_from_node(
            mirrored_member.end
        ),
    )

    layout_object, rendered_object = (
        create_member_between_nodes(
            document,
            start_node,
            end_node,
            profile=mirrored_member.profile,
            material=mirrored_member.material,
        )
    )

    ensure_mirrored_source_layout_id(
        rendered_object,
        layout_object,
    )

    return rendered_object


def mirror_member_objects(
    document,
    member_objects,
    centerline_object,
):
    """Mirror selected members across one chosen straight reference."""

    center_start, center_end = (
        centerline_nodes_from_object(
            centerline_object
        )
    )

    treatment_snapshots = (
        source_treatment_snapshots(
            document,
            member_objects,
        )
    )

    mirrored_objects = []

    for member_object in member_objects:
        mirrored_objects.append(
            mirror_member_object(
                document,
                member_object,
                center_start,
                center_end,
            )
        )

    mirrored_objects = tuple(
        mirrored_objects
    )

    preserve_centerline_mirrored_treatments(
        document,
        member_objects,
        mirrored_objects,
        treatment_snapshots,
        center_start,
        center_end,
    )

    return mirrored_objects


class MirrorReferenceDialog(
    QtGui.QDialog
):
    """Choose how selected members should be mirrored."""

    CENTERLINE = "centerline"
    REFERENCE_PLANE = "reference_plane"
    XY_PLANE = "xy_plane"
    XZ_PLANE = "xz_plane"
    YZ_PLANE = "yz_plane"

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.reference_mode = None

        self.setWindowTitle(
            "Mirror Members"
        )

        layout = QtGui.QVBoxLayout(
            self
        )

        instruction = QtGui.QLabel(
            "Choose the mirror reference for the selected members."
        )

        instruction.setWordWrap(
            True
        )

        layout.addWidget(
            instruction
        )

        centerline_button = QtGui.QPushButton(
            "Centerline"
        )

        centerline_button.setToolTip(
            "After closing this dialog, click one straight "
            "ForgeCAD member or layout line to define the centerline."
        )

        reference_plane_button = QtGui.QPushButton(
            "Reference Plane"
        )

        reference_plane_button.setToolTip(
            "After closing this dialog, select one ForgeCAD Reference Plane."
        )

        xy_button = QtGui.QPushButton(
            "XY Plane"
        )

        xz_button = QtGui.QPushButton(
            "XZ Plane"
        )

        yz_button = QtGui.QPushButton(
            "YZ Plane"
        )

        xy_button.setToolTip(
            "Mirror immediately across the global XY plane (Z=0)."
        )

        xz_button.setToolTip(
            "Mirror immediately across the global XZ plane (Y=0)."
        )

        yz_button.setToolTip(
            "Mirror immediately across the global YZ plane (X=0)."
        )

        layout.addWidget(
            centerline_button
        )

        layout.addWidget(
            reference_plane_button
        )

        layout.addWidget(
            xy_button
        )

        layout.addWidget(
            xz_button
        )

        layout.addWidget(
            yz_button
        )

        note = QtGui.QLabel(
            "Centerline uses an existing straight member or layout line. "
            "Reference Plane uses a saved ForgeCAD plane at its configured "
            "offset. XY/XZ/YZ choices use the global origin planes."
        )

        note.setWordWrap(
            True
        )

        layout.addWidget(
            note
        )

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Cancel
        )

        layout.addWidget(
            buttons
        )

        centerline_button.clicked.connect(
            self.choose_centerline
        )

        reference_plane_button.clicked.connect(
            self.choose_reference_plane
        )

        xy_button.clicked.connect(
            self.choose_xy_plane
        )

        xz_button.clicked.connect(
            self.choose_xz_plane
        )

        yz_button.clicked.connect(
            self.choose_yz_plane
        )

        buttons.rejected.connect(
            self.reject
        )

    def choose_centerline(
        self,
    ):
        """Choose an existing straight object as the mirror reference."""

        self.reference_mode = (
            self.CENTERLINE
        )

        self.accept()

    def choose_reference_plane(
        self,
    ):
        """Choose a persistent ForgeCAD Reference Plane."""

        self.reference_mode = (
            self.REFERENCE_PLANE
        )

        self.accept()

    def choose_xy_plane(
        self,
    ):
        """Choose the global XY plane."""

        self.reference_mode = (
            self.XY_PLANE
        )

        self.accept()

    def choose_xz_plane(
        self,
    ):
        """Choose the global XZ plane."""

        self.reference_mode = (
            self.XZ_PLANE
        )

        self.accept()

    def choose_yz_plane(
        self,
    ):
        """Choose the global YZ plane."""

        self.reference_mode = (
            self.YZ_PLANE
        )

        self.accept()


def mirror_member_object_across_plane(
    document,
    member_object,
    plane,
    offset=0.0,
):
    """Mirror one straight member across an axis-aligned plane."""

    source_member = (
        structural_member_from_freecad_object(
            member_object
        )
    )

    mirrored_member = (
        mirror_member_across_plane(
            source_member,
            plane,
            offset=offset,
        )
    )

    from forgecad.adapters.freecad.commands.draw_member_interactive import (
        get_or_create_node,
    )

    start_node = get_or_create_node(
        document,
        point3d_from_node(
            mirrored_member.start
        ),
    )

    end_node = get_or_create_node(
        document,
        point3d_from_node(
            mirrored_member.end
        ),
    )

    layout_object, rendered_object = (
        create_member_between_nodes(
            document,
            start_node,
            end_node,
            profile=mirrored_member.profile,
            material=mirrored_member.material,
        )
    )

    ensure_mirrored_source_layout_id(
        rendered_object,
        layout_object,
    )

    return rendered_object


def mirror_member_objects_across_plane(
    document,
    member_objects,
    plane,
    offset=0.0,
):
    """Mirror selected straight members across one axis-aligned plane."""

    treatment_snapshots = (
        source_treatment_snapshots(
            document,
            member_objects,
        )
    )

    mirrored_objects = []

    for member_object in member_objects:
        mirrored_objects.append(
            mirror_member_object_across_plane(
                document,
                member_object,
                plane,
                offset=offset,
            )
        )

    mirrored_objects = tuple(
        mirrored_objects
    )

    preserve_plane_mirrored_treatments(
        document,
        member_objects,
        mirrored_objects,
        treatment_snapshots,
        plane,
        offset=offset,
    )

    return mirrored_objects


def finish_mirror_result(
    document,
    mirrored_objects,
):
    """Select mirrored results and refresh the FreeCAD view."""

    FreeCADGui.Selection.clearSelection()

    for obj in mirrored_objects:
        FreeCADGui.Selection.addSelection(
            obj
        )

    document.recompute()

    try:
        FreeCADGui.activeDocument().activeView().fitAll()
    except (
        AttributeError,
        RuntimeError,
    ):
        pass


class MirrorCenterlineSelectionObserver:
    """Wait for one centerline selection, then complete the mirror."""

    def __init__(
        self,
        tool,
    ):
        self.tool = tool

    def addSelection(
        self,
        document_name,
        object_name,
        sub_name,
        point,
    ):
        """Accept the first selected straight reference object."""

        self.tool.accept_selection(
            document_name,
            object_name,
        )


class InteractiveMirrorMembersTool:
    """Capture source members, then wait for a centerline selection."""

    def __init__(
        self,
        document,
        member_objects,
    ):
        self.document = document
        self.member_objects = tuple(
            member_objects
        )

        self.observer = (
            MirrorCenterlineSelectionObserver(
                self
            )
        )

        self.status_bar = None
        self.running = False

    def start(self):
        """Start waiting for the builder to select the mirror centerline."""

        self.status_bar = (
            FreeCADGui.getMainWindow().statusBar()
        )

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.Selection.addObserver(
            self.observer
        )

        self.running = True

        self.show_status(
            "ForgeCAD Mirror Members: "
            "SELECT CENTERLINE NOW - click one straight "
            "member or layout line."
        )

    def stop(self):
        """Stop the temporary centerline-selection mode."""

        global _active_tool

        if self.running:
            try:
                FreeCADGui.Selection.removeObserver(
                    self.observer
                )
            except (
                AttributeError,
                RuntimeError,
            ):
                pass

        self.running = False

        if self.status_bar is not None:
            self.status_bar.clearMessage()

        if _active_tool is self:
            _active_tool = None

    def show_status(
        self,
        message,
    ):
        """Show one instruction in the FreeCAD status bar."""

        if self.status_bar is not None:
            self.status_bar.showMessage(
                message
            )

    def object_from_selection(
        self,
        document_name,
        object_name,
    ):
        """Resolve the object selected by the FreeCAD selection observer."""

        document = self.document

        if (
            document is None
            or str(
                getattr(
                    document,
                    "Name",
                    "",
                )
            )
            != str(
                document_name
            )
        ):
            return None

        return document.getObject(
            object_name
        )

    def accept_selection(
        self,
        document_name,
        object_name,
    ):
        """Use the selected object as centerline and complete the mirror."""

        if not self.running:
            return

        reference = self.object_from_selection(
            document_name,
            object_name,
        )

        if not is_centerline_reference(
            reference
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select Centerline",
                (
                    "Select one straight ForgeCAD member "
                    "or layout line to use as the mirror centerline."
                ),
            )

            FreeCADGui.Selection.clearSelection()

            self.show_status(
                "ForgeCAD Mirror Members: "
                "that object cannot define a centerline. "
                "Click one straight member or layout line."
            )
            return

        try:
            mirrored_objects = (
                mirror_member_objects(
                    self.document,
                    self.member_objects,
                    reference,
                )
            )

        except (
            ValueError,
            KeyError,
            AttributeError,
        ) as error:
            self.stop()

            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Mirror Members Failed",
                str(
                    error
                ),
            )
            return

        self.stop()

        finish_mirror_result(
            self.document,
            mirrored_objects,
        )



class MirrorReferencePlaneSelectionObserver:
    """Wait for one ForgeCAD Reference Plane selection."""

    def __init__(
        self,
        tool,
    ):
        self.tool = tool

    def addSelection(
        self,
        document_name,
        object_name,
        sub_name,
        point,
    ):
        self.tool.accept_selection(
            document_name,
            object_name,
        )


class InteractiveMirrorReferencePlaneTool:
    """Capture source members, then wait for a Reference Plane selection."""

    def __init__(
        self,
        document,
        member_objects,
    ):
        self.document = document
        self.member_objects = tuple(
            member_objects
        )

        self.observer = (
            MirrorReferencePlaneSelectionObserver(
                self
            )
        )

        self.status_bar = None
        self.running = False

    def start(
        self,
    ):
        self.status_bar = (
            FreeCADGui.getMainWindow().statusBar()
        )

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.Selection.addObserver(
            self.observer
        )

        self.running = True

        self.show_status(
            "ForgeCAD Mirror Members: SELECT REFERENCE PLANE NOW - "
            "click one plane in the Reference Geometry group."
        )

    def stop(
        self,
    ):
        global _active_tool

        if self.running:
            try:
                FreeCADGui.Selection.removeObserver(
                    self.observer
                )
            except (
                AttributeError,
                RuntimeError,
            ):
                pass

        self.running = False

        if self.status_bar is not None:
            self.status_bar.clearMessage()

        if _active_tool is self:
            _active_tool = None

    def show_status(
        self,
        message,
    ):
        if self.status_bar is not None:
            self.status_bar.showMessage(
                message
            )

    def object_from_selection(
        self,
        document_name,
        object_name,
    ):
        document = self.document

        if (
            document is None
            or str(
                getattr(
                    document,
                    "Name",
                    "",
                )
            )
            != str(
                document_name
            )
        ):
            return None

        return document.getObject(
            object_name
        )

    def accept_selection(
        self,
        document_name,
        object_name,
    ):
        if not self.running:
            return

        reference = self.object_from_selection(
            document_name,
            object_name,
        )

        if not is_reference_plane_object(
            reference
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select Reference Plane",
                (
                    "Select one ForgeCAD Reference Plane from the "
                    "Reference Geometry group."
                ),
            )

            FreeCADGui.Selection.clearSelection()

            self.show_status(
                "ForgeCAD Mirror Members: that object is not a "
                "Reference Plane. Select one Reference Geometry plane."
            )
            return

        try:
            plane = reference_plane_from_object(
                reference
            )

            mirrored_objects = (
                mirror_member_objects_across_plane(
                    self.document,
                    self.member_objects,
                    plane.orientation.value,
                    offset=plane.offset,
                )
            )

        except (
            ValueError,
            KeyError,
            AttributeError,
        ) as error:
            self.stop()

            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Mirror Members Failed",
                str(
                    error
                ),
            )
            return

        self.stop()

        finish_mirror_result(
            self.document,
            mirrored_objects,
        )


class MirrorMembersCommand:
    """Mirror selected straight members across a builder-selected centerline."""

    def GetResources(self):
        return {
            "MenuText": "Mirror Members",
            "ToolTip": (
                "Mirror selected ForgeCAD members across a centerline, "
                "global plane, or saved ForgeCAD Reference Plane"
            ),
        }

    def Activated(self):
        global _active_tool

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

        if not selection:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select Members",
                (
                    "Select one or more ForgeCAD straight "
                    "members to mirror, then run Mirror Members."
                ),
            )
            return

        members = [
            obj
            for obj in selection
            if is_forgecad_member(
                obj
            )
        ]

        if len(
            members
        ) != len(
            selection
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                (
                    "Before starting Mirror Members, select only "
                    "the straight ForgeCAD members you want to mirror."
                ),
            )
            return

        dialog = MirrorReferenceDialog(
            FreeCADGui.getMainWindow()
        )

        if (
            dialog.exec_()
            != QtGui.QDialog.Accepted
        ):
            return

        if (
            dialog.reference_mode
            == MirrorReferenceDialog.CENTERLINE
        ):
            if _active_tool is not None:
                _active_tool.stop()

            _active_tool = (
                InteractiveMirrorMembersTool(
                    document,
                    members,
                )
            )

            _active_tool.start()

            return

        if (
            dialog.reference_mode
            == MirrorReferenceDialog.REFERENCE_PLANE
        ):
            if _active_tool is not None:
                _active_tool.stop()

            _active_tool = (
                InteractiveMirrorReferencePlaneTool(
                    document,
                    members,
                )
            )

            _active_tool.start()

            return

        plane_by_mode = {
            MirrorReferenceDialog.XY_PLANE: "XY",
            MirrorReferenceDialog.XZ_PLANE: "XZ",
            MirrorReferenceDialog.YZ_PLANE: "YZ",
        }

        plane = plane_by_mode.get(
            dialog.reference_mode
        )

        if plane is None:
            return

        try:
            mirrored_objects = (
                mirror_member_objects_across_plane(
                    document,
                    members,
                    plane,
                )
            )

        except (
            ValueError,
            KeyError,
            AttributeError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Mirror Members Failed",
                str(
                    error
                ),
            )
            return

        finish_mirror_result(
            document,
            mirrored_objects,
        )

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Mirror Members command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        MirrorMembersCommand(),
    )
