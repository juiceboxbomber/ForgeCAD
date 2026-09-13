"""FreeCAD command for converting one simple straight joint into a bend."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.fabrication import (
    Bend,
    BentTube,
    Node,
    StraightRun,
)

from forgecad.adapters.freecad.bent_tube_object import (
    create_bent_tube_object,
    ensure_bent_tube_design_joint_links,
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
    is_forgecad_bent_member,
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
from forgecad.services.multi_joint_bend import (
    build_multi_joint_bent_tube,
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


def is_joint_node_selection(
    obj,
):
    """Return True when an object is a persistent ForgeCAD node."""

    if obj is None:
        return False

    return (
        hasattr(
            obj,
            "NodeID",
        )
        and hasattr(
            obj,
            "Position",
        )
    )


def selected_joint_object():
    """Return exactly one selected ForgeCAD joint node or marker."""

    selection = list(
        FreeCADGui.Selection.getSelection()
    )

    if len(
        selection
    ) != 1:
        return None

    selected = selection[
        0
    ]

    if (
        is_joint_marker(
            selected
        )
        or is_joint_node_selection(
            selected
        )
    ):
        return selected

    return None


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


def joint_status_for_node(
    document,
    node_object,
    tolerance=1e-6,
):
    """Resolve one persistent ForgeCAD node to current joint review data."""

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if not is_joint_node_selection(
        node_object
    ):
        raise ValueError(
            "Select one ForgeCAD joint node."
        )

    position = node_object.Position

    review = joint_review_for_document(
        document
    )

    for item in review.joints:
        joint_node = item.joint.node

        if (
            abs(
                float(
                    joint_node.x
                )
                - float(
                    position.x
                )
            )
            <= tolerance
            and abs(
                float(
                    joint_node.y
                )
                - float(
                    position.y
                )
            )
            <= tolerance
            and abs(
                float(
                    joint_node.z
                )
                - float(
                    position.z
                )
            )
            <= tolerance
        ):
            return item

    raise ValueError(
        "The selected node is not a current ForgeCAD joint."
    )


def joint_status_for_selection(
    document,
    selected_object,
):
    """Resolve either a joint-tree marker or persistent node to joint status."""

    if is_joint_marker(
        selected_object
    ):
        return joint_status_for_marker(
            document,
            selected_object,
        )

    if is_joint_node_selection(
        selected_object
    ):
        return joint_status_for_node(
            document,
            selected_object,
        )

    raise ValueError(
        "Select one ForgeCAD joint node or Joints-tree item."
    )


def joint_selection_label(
    selected_object,
    joint_status,
):
    """Return a useful label for the Convert Joint to Bend dialog."""

    if is_joint_marker(
        selected_object
    ):
        joint_id = str(
            getattr(
                selected_object,
                "JointID",
                "",
            )
        ).strip()

        if joint_id:
            return joint_id

    node_id = str(
        getattr(
            selected_object,
            "NodeID",
            "",
        )
    ).strip()

    if node_id:
        return node_id

    return str(
        getattr(
            joint_status,
            "node_key",
            "Joint",
        )
    )


def joint_conversion_mode(
    member_objects,
):
    """
    Return the supported Convert Joint to Bend path for two FreeCAD objects.

    "create" is the original two-straight-member conversion.
    "extend" grows one existing bent tube through an adjacent straight member.
    """

    objects = tuple(
        member_objects
    )

    if len(
        objects
    ) != 2:
        raise ValueError(
            "Convert Joint to Bend requires exactly two structural members."
        )

    bent_count = sum(
        1
        for obj in objects
        if is_forgecad_bent_member(
            obj
        )
        or (
            getattr(
                obj,
                "Proxy",
                None,
            )
            is not None
            and hasattr(
                getattr(
                    obj,
                    "Proxy",
                    None,
                ),
                "replace_tube_definition",
            )
        )
    )

    straight_count = sum(
        1
        for obj in objects
        if is_forgecad_member(
            obj
        )
        or (
            hasattr(
                obj,
                "MemberID",
            )
            and hasattr(
                obj,
                "SourceLayoutID",
            )
        )
    )

    if (
        bent_count == 0
        and straight_count == 2
    ):
        return "create"

    if (
        bent_count == 1
        and straight_count == 1
    ):
        return "extend"

    raise ValueError(
        "Convert Joint to Bend currently supports either "
        "two straight members or one bent tube plus one straight member."
    )


def is_extendable_bent_joint_objects(
    member_objects,
):
    """
    Return True for exactly one bent tube plus one straight member.

    This identifies the next corner of one continuous fabricated tube
    after an earlier straight-to-bend conversion. Two straight members
    continue to use the original conversion path. Two bent members are
    intentionally not merged here.
    """

    objects = tuple(
        member_objects
    )

    if len(
        objects
    ) != 2:
        return False

    bent_count = sum(
        1
        for obj in objects
        if is_forgecad_bent_member(
            obj
        )
    )

    straight_count = sum(
        1
        for obj in objects
        if is_forgecad_member(
            obj
        )
    )

    return (
        bent_count == 1
        and straight_count == 1
    )


def append_bend_to_tube(
    tube,
    final_run_length_mm,
    bend_angle_degrees,
    centerline_radius_mm,
    rotation_degrees=0.0,
):
    """
    Return a new BentTube with one bend and one final straight run appended.

    The original BentTube is immutable and remains unchanged.
    """

    if not isinstance(
        tube,
        BentTube,
    ):
        raise TypeError(
            "append_bend_to_tube requires a BentTube."
        )

    final_run_length = float(
        final_run_length_mm
    )

    if final_run_length <= 0.0:
        raise ValueError(
            "Final straight run length must be greater than zero."
        )

    bend = Bend(
        angle_degrees=float(
            bend_angle_degrees
        ),
        centerline_radius=float(
            centerline_radius_mm
        ),
        rotation_degrees=float(
            rotation_degrees
        ),
    )

    return BentTube(
        straight_runs=(
            *tube.straight_runs,
            StraightRun(
                final_run_length
            ),
        ),
        bends=(
            *tube.bends,
            bend,
        ),
        profile=tube.profile,
        material=tube.material,
    )


def freecad_structural_objects_for_joint(
    document,
    joint,
):
    """
    Return FreeCAD structural objects represented by a simple joint.

    Mapping follows ``joint.members`` order exactly. Both generated straight
    members and persistent bent-tube objects are eligible because
    ``frame_member_objects()`` already exposes both structural object types.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if not joint.is_simple:
        raise ValueError(
            "Convert Joint to Bend requires exactly two members."
        )

    available = []

    for obj in frame_member_objects(
        document
    ):
        try:
            domain_member = (
                structural_member_from_freecad_object(
                    obj
                )
            )
        except ValueError:
            continue

        available.append(
            (
                obj,
                domain_member,
            )
        )

    matches = []

    used_indexes = set()

    for requested_member in joint.members:
        matched_object = None

        for index, (
            obj,
            domain_member,
        ) in enumerate(
            available
        ):
            if index in used_indexes:
                continue

            if domain_member == requested_member:
                matched_object = obj
                used_indexes.add(
                    index
                )
                break

        if matched_object is None:
            raise ValueError(
                "ForgeCAD could not map the joint to exactly two "
                "structural members."
            )

        matches.append(
            matched_object
        )

    if len(
        matches
    ) != 2:
        raise ValueError(
            "ForgeCAD could not map the joint to exactly two "
            "structural members."
        )

    return tuple(
        matches
    )


def freecad_members_for_joint(
    document,
    joint,
):
    """
    Return the exact two straight FreeCAD members represented by a joint.

    This preserves the original straight-to-bend conversion path while
    delegating structural-object mapping to the generalized helper.
    """

    matches = (
        freecad_structural_objects_for_joint(
            document,
            joint,
        )
    )

    if not all(
        is_forgecad_member(
            obj
        )
        for obj in matches
    ):
        raise ValueError(
            "ForgeCAD could not map the joint to exactly two straight members."
        )

    return matches


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


def extend_existing_bent_object(
    document,
    bent_object,
    straight_object,
    replacement_tube,
    design_joint_node,
    new_end_node,
):
    """
    Extend one existing bent-tube document object through an adjacent joint.

    The bent object's document identity is preserved. The adjoining straight
    member is consumed, its source-layout object is transferred to the bent
    tube's ownership list, the new design joint is stored in path order, and
    the bent tube's EndNode advances to the straight member's outer endpoint.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if bent_object is None:
        raise ValueError(
            "An existing ForgeCAD bent tube is required."
        )

    if straight_object is None:
        raise ValueError(
            "An adjoining ForgeCAD straight member is required."
        )

    proxy = getattr(
        bent_object,
        "Proxy",
        None,
    )

    if (
        proxy is None
        or not hasattr(
            proxy,
            "replace_tube_definition",
        )
    ):
        raise ValueError(
            "The selected bent tube is not parametric."
        )

    existing_design_joints = []

    index = 1

    while True:
        property_name = (
            f"DesignJointNode{index}"
        )

        if not hasattr(
            bent_object,
            property_name,
        ):
            break

        joint_node = getattr(
            bent_object,
            property_name,
            None,
        )

        if joint_node is not None:
            existing_design_joints.append(
                joint_node
            )

        index += 1

    if not existing_design_joints:
        legacy_joint = getattr(
            bent_object,
            "DesignJointNode",
            None,
        )

        if legacy_joint is not None:
            existing_design_joints.append(
                legacy_joint
            )

    if design_joint_node is None:
        raise ValueError(
            "A design joint node is required."
        )

    if (
        not existing_design_joints
        or existing_design_joints[
            -1
        ]
        is not design_joint_node
    ):
        existing_design_joints.append(
            design_joint_node
        )

    ensure_bent_tube_design_joint_links(
        bent_object,
        tuple(
            existing_design_joints
        ),
    )

    source_layouts = list(
        getattr(
            bent_object,
            "SourceLayoutLines",
            (),
        )
    )

    layout_id = str(
        getattr(
            straight_object,
            "SourceLayoutID",
            "",
        )
    ).strip()

    if layout_id:
        layout_object = layout_object_for_id(
            document,
            layout_id,
        )

        # Tests may use the layout ID itself as the lightweight ownership
        # stand-in when no real layout object exists.
        layout_reference = (
            layout_object
            if layout_object is not None
            else layout_id
        )

        if layout_reference not in source_layouts:
            source_layouts.append(
                layout_reference
            )

    bent_object.SourceLayoutLines = list(
        source_layouts
    )

    if new_end_node is None:
        raise ValueError(
            "The extended bent tube requires a new endpoint node."
        )

    bent_object.EndNode = (
        new_end_node
    )

    proxy.replace_tube_definition(
        bent_object,
        replacement_tube,
    )

    frame_group = document.getObject(
        "ForgeCADFrame"
    )

    if frame_group is not None:
        try:
            frame_group.removeObject(
                straight_object
            )
        except Exception:
            pass

    object_name = str(
        getattr(
            straight_object,
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

    document.recompute()

    return bent_object



def prepend_existing_bent_object(
    document,
    bent_object,
    straight_object,
    replacement_tube,
    design_joint_node,
    new_start_node,
):
    """
    Prepend one adjoining straight member to an existing bent-tube object.

    The bent object's document identity is preserved. The previous StartNode
    becomes the first design joint, existing design joints shift forward in
    path order, the straight member's outer endpoint becomes the new StartNode,
    and the straight member is removed while its source layout remains owned
    by the bent tube.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    if bent_object is None:
        raise ValueError(
            "An existing ForgeCAD bent tube is required."
        )

    if straight_object is None:
        raise ValueError(
            "An adjoining ForgeCAD straight member is required."
        )

    proxy = getattr(
        bent_object,
        "Proxy",
        None,
    )

    if (
        proxy is None
        or not hasattr(
            proxy,
            "replace_tube_definition",
        )
    ):
        raise ValueError(
            "The selected bent tube is not parametric."
        )

    if design_joint_node is None:
        raise ValueError(
            "A design joint node is required."
        )

    if new_start_node is None:
        raise ValueError(
            "The extended bent tube requires a new start endpoint node."
        )

    existing_design_joints = list(
        design_joint_node_objects(
            bent_object
        )
    )

    ordered_design_joints = [
        design_joint_node,
    ]

    for joint_node in existing_design_joints:
        if joint_node is design_joint_node:
            continue

        ordered_design_joints.append(
            joint_node
        )

    ensure_bent_tube_design_joint_links(
        bent_object,
        tuple(
            ordered_design_joints
        ),
    )

    source_layouts = list(
        getattr(
            bent_object,
            "SourceLayoutLines",
            (),
        )
    )

    layout_id = str(
        getattr(
            straight_object,
            "SourceLayoutID",
            "",
        )
    ).strip()

    if layout_id:
        layout_object = layout_object_for_id(
            document,
            layout_id,
        )

        # Tests may use the layout ID itself as the lightweight ownership
        # stand-in when no real layout object exists.
        layout_reference = (
            layout_object
            if layout_object is not None
            else layout_id
        )

        if layout_reference not in source_layouts:
            source_layouts.append(
                layout_reference
            )

    bent_object.SourceLayoutLines = list(
        source_layouts
    )

    old_end_node = getattr(
        bent_object,
        "EndNode",
        None,
    )

    if old_end_node is None:
        raise ValueError(
            "The bent tube has no persistent EndNode."
        )

    ensure_bent_tube_node_links(
        bent_object,
        new_start_node,
        old_end_node,
    )

    proxy.replace_tube_definition(
        bent_object,
        replacement_tube,
    )

    frame_group = document.getObject(
        "ForgeCADFrame"
    )

    if frame_group is not None:
        try:
            frame_group.removeObject(
                straight_object
            )
        except Exception:
            pass

    object_name = str(
        getattr(
            straight_object,
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

    document.recompute()

    return bent_object

def fabrication_node_from_object(
    node_object,
):
    """Return a domain Node from one persistent FreeCAD node object."""

    if node_object is None:
        raise ValueError(
            "A persistent ForgeCAD node is required."
        )

    position = getattr(
        node_object,
        "Position",
        None,
    )

    if position is None:
        raise ValueError(
            "ForgeCAD node has no Position."
        )

    return Node(
        float(
            position.x
        ),
        float(
            position.y
        ),
        float(
            position.z
        ),
    )


def design_joint_node_objects(
    bent_object,
):
    """Return ordered persistent design-joint nodes for one bent tube."""

    joints = []

    index = 1

    while True:
        property_name = (
            f"DesignJointNode{index}"
        )

        if not hasattr(
            bent_object,
            property_name,
        ):
            break

        node_object = getattr(
            bent_object,
            property_name,
            None,
        )

        if node_object is not None:
            joints.append(
                node_object
            )

        index += 1

    if not joints:
        legacy_joint = getattr(
            bent_object,
            "DesignJointNode",
            None,
        )

        if legacy_joint is not None:
            joints.append(
                legacy_joint
            )

    return tuple(
        joints
    )


def _node_object_matches_joint(
    node_object,
    joint_node,
    tolerance=1e-6,
):
    """Return True when a persistent node occupies one domain joint point."""

    if node_object is None:
        return False

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


def extend_bent_tube_from_joint(
    document,
    joint_status,
    centerline_radius_mm,
):
    """
    Extend an existing bent tube through one adjoining straight-member joint.

    The selected joint may be at either persistent endpoint. EndNode extension
    appends the new bend to the existing path. StartNode extension prepends the
    new bend while preserving the same bent-object identity and old EndNode.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    joint = joint_status.joint

    member_objects = (
        freecad_structural_objects_for_joint(
            document,
            joint,
        )
    )

    if (
        joint_conversion_mode(
            member_objects
        )
        != "extend"
    ):
        raise ValueError(
            "The selected joint is not an extendable bent-tube joint."
        )

    bent_object = next(
        (
            obj
            for obj in member_objects
            if is_forgecad_bent_member(
                obj
            )
            or (
                getattr(
                    obj,
                    "Proxy",
                    None,
                )
                is not None
                and hasattr(
                    getattr(
                        obj,
                        "Proxy",
                        None,
                    ),
                    "replace_tube_definition",
                )
            )
        ),
        None,
    )

    straight_object = next(
        (
            obj
            for obj in member_objects
            if obj is not bent_object
            and (
                is_forgecad_member(
                    obj
                )
                or (
                    hasattr(
                        obj,
                        "MemberID",
                    )
                    and hasattr(
                        obj,
                        "SourceLayoutID",
                    )
                )
            )
        ),
        None,
    )

    if (
        bent_object is None
        or straight_object is None
    ):
        raise ValueError(
            "ForgeCAD could not identify the bent and straight members."
        )

    current_start_node = getattr(
        bent_object,
        "StartNode",
        None,
    )
    current_end_node = getattr(
        bent_object,
        "EndNode",
        None,
    )

    matches_start = _node_object_matches_joint(
        current_start_node,
        joint.node,
    )
    matches_end = _node_object_matches_joint(
        current_end_node,
        joint.node,
    )

    if not matches_start and not matches_end:
        raise ValueError(
            "Bent-tube extension requires the selected joint "
            "to be at the bent tube's StartNode or EndNode."
        )

    if matches_start and matches_end:
        raise ValueError(
            "ForgeCAD cannot extend a bent tube whose StartNode and EndNode "
            "occupy the same selected joint."
        )

    design_node = joint_node_object(
        document,
        joint.node,
    )

    if design_node is None:
        raise ValueError(
            "ForgeCAD could not find the persistent node for this joint."
        )

    outer_node = outer_node_object(
        straight_object,
        joint.node,
    )

    proxy = getattr(
        bent_object,
        "Proxy",
        None,
    )

    if (
        proxy is None
        or not hasattr(
            proxy,
            "_tube_from_properties",
        )
    ):
        raise ValueError(
            "The selected bent tube is not parametric."
        )

    current_tube = (
        proxy._tube_from_properties(
            bent_object
        )
    )

    existing_joint_nodes = list(
        design_joint_node_objects(
            bent_object
        )
    )

    existing_radii = tuple(
        float(
            bend.centerline_radius
        )
        for bend in current_tube.bends
    )

    if matches_start:
        if current_end_node is None:
            raise ValueError(
                "The bent tube has no persistent EndNode."
            )

        design_path_nodes = (
            outer_node,
            design_node,
            *existing_joint_nodes,
            current_end_node,
        )

        radii = (
            float(
                centerline_radius_mm
            ),
            *existing_radii,
        )

        replacement_tube = (
            build_multi_joint_bent_tube(
                nodes=tuple(
                    fabrication_node_from_object(
                        node_object
                    )
                    for node_object in design_path_nodes
                ),
                centerline_radii_mm=radii,
                profile=current_tube.profile,
                material=current_tube.material,
            )
        )

        result = prepend_existing_bent_object(
            document=document,
            bent_object=bent_object,
            straight_object=straight_object,
            replacement_tube=replacement_tube,
            design_joint_node=design_node,
            new_start_node=outer_node,
        )

    else:
        if current_start_node is None:
            raise ValueError(
                "The bent tube has no persistent StartNode."
            )

        ordered_joint_nodes = list(
            existing_joint_nodes
        )

        if (
            not ordered_joint_nodes
            or ordered_joint_nodes[
                -1
            ]
            is not design_node
        ):
            ordered_joint_nodes.append(
                design_node
            )

        design_path_nodes = (
            current_start_node,
            *ordered_joint_nodes,
            outer_node,
        )

        radii = (
            *existing_radii,
            float(
                centerline_radius_mm
            ),
        )

        replacement_tube = (
            build_multi_joint_bent_tube(
                nodes=tuple(
                    fabrication_node_from_object(
                        node_object
                    )
                    for node_object in design_path_nodes
                ),
                centerline_radii_mm=radii,
                profile=current_tube.profile,
                material=current_tube.material,
            )
        )

        result = extend_existing_bent_object(
            document=document,
            bent_object=bent_object,
            straight_object=straight_object,
            replacement_tube=replacement_tube,
            design_joint_node=design_node,
            new_end_node=outer_node,
        )

    hide_design_geometry_for_bend(
        document,
        (
            straight_object,
        ),
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

    return result

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
                "Convert a straight joint to a bend or extend "
                "an existing continuous bent tube"
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

        selected_object = selected_joint_object()

        if selected_object is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select One Joint",
                (
                    "Select exactly one ForgeCAD joint node in the 3D view "
                    "or one joint item in the Joints tree, then run "
                    "Convert Joint to Bend."
                ),
            )
            return

        try:
            joint_status = joint_status_for_selection(
                document,
                selected_object,
            )

            if not joint_status.joint.is_simple:
                raise ValueError(
                    "Convert Joint to Bend requires exactly two members."
                )

            structural_objects = (
                freecad_structural_objects_for_joint(
                    document,
                    joint_status.joint,
                )
            )

            conversion_mode = (
                joint_conversion_mode(
                    structural_objects
                )
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
            joint_selection_label(
                selected_object,
                joint_status,
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

            if conversion_mode == "create":
                bent_object = (
                    create_bent_tube_from_joint(
                        document,
                        joint_status,
                        dialog.radius_box.value(),
                    )
                )

            else:
                bent_object = (
                    extend_bent_tube_from_joint(
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
