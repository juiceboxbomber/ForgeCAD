"""FreeCAD integration helpers for splitting ForgeCAD members."""

import FreeCAD

from forgecad import LayoutLine
from forgecad.geometry import Point3D, Vector3D
from forgecad.adapters.freecad.bent_tube_object import (
    create_bent_tube_object,
    ensure_bent_tube_design_joint_links,
    ensure_bent_tube_node_links,
)
from forgecad.adapters.freecad.commands.convert_joint_to_bend import (
    set_bent_fabrication_endpoint_ids,
    store_bend_design_references,
)
from forgecad.adapters.freecad.commands.create_member_between_nodes import (
    create_member_between_nodes,
)
from forgecad.adapters.freecad.commands.draw_layout_line import (
    create_layout_line_object,
    ensure_layout_id,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)
from forgecad.adapters.freecad.fabrication_refresh import (
    refresh_fabrication_for_document,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    is_forgecad_bent_member,
    structural_member_from_freecad_object,
)
from forgecad.adapters.freecad.member_removal import (
    remove_member_and_unused_layout,
)
from forgecad.adapters.freecad.topology_refresh import (
    refresh_joint_topology,
)
from forgecad.services.bent_tube_path import (
    CircularArcPathSegment,
    StraightPathSegment,
    build_bent_tube_centerline,
)
from forgecad.services.member_split import (
    split_bent_tube,
    split_member,
)


def _point_from_vector(vector):
    return Point3D(
        float(vector.x),
        float(vector.y),
        float(vector.z),
    )


def _vector3d_from_vector(vector):
    return Vector3D(
        float(vector.x),
        float(vector.y),
        float(vector.z),
    )


def _freecad_vector(vector):
    return FreeCAD.Vector(
        float(vector.x),
        float(vector.y),
        float(vector.z),
    )


def _design_joint_nodes(member_object):
    nodes = []

    legacy = getattr(
        member_object,
        "DesignJointNode",
        None,
    )

    if legacy is not None:
        nodes.append(legacy)

    index = 1

    while True:
        property_name = f"DesignJointNode{index}"

        if not hasattr(
            member_object,
            property_name,
        ):
            break

        node = getattr(
            member_object,
            property_name,
            None,
        )

        if (
            node is not None
            and node not in nodes
        ):
            nodes.append(node)

        index += 1

    return tuple(nodes)


def _remove_from_group(
    group,
    obj,
):
    if (
        group is None
        or obj is None
    ):
        return

    try:
        group.removeObject(obj)
    except Exception:
        pass


def _layout_path_endpoints(
    layout_object,
    segment_start,
    segment_end,
):
    """Return source-layout endpoints ordered along the bent-tube path."""

    layout_start = _point_from_vector(
        layout_object.StartPoint
    )
    layout_end = _point_from_vector(
        layout_object.EndPoint
    )

    path_direction = segment_start.vector_to(
        segment_end
    )
    layout_direction = layout_start.vector_to(
        layout_end
    )

    if (
        layout_direction.dot(
            path_direction
        )
        >= 0.0
    ):
        return (
            layout_start,
            layout_end,
        )

    return (
        layout_end,
        layout_start,
    )


def _create_split_source_layouts(
    document,
    source_layout,
    split_point,
    segment_start,
    segment_end,
    *,
    preserve_original_id_on_second=False,
):
    """Replace one hidden source layout with two lines at split_point."""

    tree = initialize_project_tree(
        document
    )
    layout_group = tree[
        "Layout"
    ]

    path_start, path_end = (
        _layout_path_endpoints(
            source_layout,
            segment_start,
            segment_end,
        )
    )

    original_layout_id = str(
        ensure_layout_id(
            source_layout
        )
    ).strip()

    first_layout = (
        create_layout_line_object(
            document,
            LayoutLine(
                start=path_start,
                end=split_point,
            ),
        )
    )

    second_layout = (
        create_layout_line_object(
            document,
            LayoutLine(
                start=split_point,
                end=path_end,
            ),
        )
    )

    layout_group.addObject(
        first_layout
    )
    layout_group.addObject(
        second_layout
    )

    if preserve_original_id_on_second:
        second_layout.LayoutID = original_layout_id
    else:
        first_layout.LayoutID = original_layout_id

    for layout in (
        first_layout,
        second_layout,
    ):
        try:
            layout.ViewObject.Visibility = False
        except Exception:
            pass

    _remove_from_group(
        layout_group,
        source_layout,
    )

    document.removeObject(
        source_layout.Name
    )

    return (
        first_layout,
        second_layout,
    )


def _second_split_frame(
    tube,
    run_index,
    split_point,
    start_point,
    initial_direction,
    initial_bend_normal,
):
    """Return the local start frame for the second split bent tube."""

    centerline = build_bent_tube_centerline(
        tube,
        start_point=start_point,
        initial_direction=initial_direction,
        initial_bend_normal=initial_bend_normal,
    )

    straight_segments = [
        segment
        for segment in centerline.segments
        if isinstance(
            segment,
            StraightPathSegment,
        )
    ]

    source_segment = straight_segments[
        run_index
    ]

    direction = (
        source_segment.start
        .vector_to(
            source_segment.end
        )
        .normalized()
    )

    if run_index == 0:
        reference_normal = (
            initial_bend_normal
        )
    else:
        arcs = [
            segment
            for segment in centerline.segments
            if isinstance(
                segment,
                CircularArcPathSegment,
            )
        ]

        reference_normal = arcs[
            run_index - 1
        ].normal

    return (
        split_point,
        direction,
        reference_normal,
        source_segment,
    )


def _configure_bent_object(
    obj,
    tube,
    *,
    tube_name,
    start_point,
    initial_direction,
    initial_bend_normal,
    start_node,
    end_node,
    source_layouts,
    design_nodes,
    start_layout_id,
    end_layout_id,
):
    obj.TubeName = tube_name
    obj.StartPoint = _freecad_vector(
        start_point
    )
    obj.InitialDirection = _freecad_vector(
        initial_direction
    )
    obj.InitialBendNormal = _freecad_vector(
        initial_bend_normal
    )

    ensure_bent_tube_node_links(
        obj,
        start_node,
        end_node,
    )

    legacy_design_node = (
        design_nodes[0]
        if design_nodes
        else None
    )

    store_bend_design_references(
        obj,
        source_layouts,
        legacy_design_node,
    )

    ensure_bent_tube_design_joint_links(
        obj,
        design_nodes,
    )

    set_bent_fabrication_endpoint_ids(
        obj,
        start_layout_id=start_layout_id,
        end_layout_id=end_layout_id,
    )

    obj.Proxy.replace_tube_definition(
        obj,
        tube,
    )
    obj.Proxy.update_shape(
        obj
    )

    return obj


def _restore_split_node_position(
    split_node,
    split_point,
    first_split_layout,
    second_split_layout,
):
    """Keep the shared split node fixed at the authoritative split point."""

    proxy = getattr(
        split_node,
        "Proxy",
        None,
    )
    previous_updating = getattr(
        proxy,
        "_updating",
        None,
    )

    if (
        proxy is not None
        and previous_updating is not None
    ):
        proxy._updating = True

    try:
        split_node.Placement.Base = _freecad_vector(
            split_point
        )
        split_node.Position = _freecad_vector(
            split_point
        )

        for name, value in (
            ("X", split_point.x),
            ("Y", split_point.y),
            ("Z", split_point.z),
        ):
            if hasattr(
                split_node,
                name,
            ):
                setattr(
                    split_node,
                    name,
                    float(value),
                )

        first_split_layout.EndPoint = _freecad_vector(
            split_point
        )
        second_split_layout.StartPoint = _freecad_vector(
            split_point
        )

    finally:
        if (
            proxy is not None
            and previous_updating is not None
        ):
            proxy._updating = previous_updating


def _resolved_bent_definition(
    member_object,
):
    """
    Return the current solved BentTube definition and local start frame.

    Converted bends are controlled by StartNode / DesignJointNode(s) / EndNode.
    Force the existing bent proxy to solve those authoritative links first so
    Split Member never uses stale RunNLength / InitialDirection properties.
    """

    proxy = getattr(
        member_object,
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
            "Bent member is missing its parametric tube definition."
        )

    update_shape = getattr(
        proxy,
        "update_shape",
        None,
    )

    if update_shape is not None:
        update_shape(
            member_object
        )

    tube = proxy._tube_from_properties(
        member_object
    )

    start_point = _point_from_vector(
        member_object.StartPoint
    )

    initial_direction = (
        _vector3d_from_vector(
            member_object.InitialDirection
        )
    )

    initial_bend_normal = (
        _vector3d_from_vector(
            member_object.InitialBendNormal
        )
    )

    return (
        tube,
        start_point,
        initial_direction,
        initial_bend_normal,
    )



def split_bent_member_object(
    document,
    member_object,
    split_point,
):
    """Replace one converted bent tube with two persistent bent tubes."""

    if document is None:
        raise ValueError(
            "Split Member requires an active document."
        )

    if not is_forgecad_bent_member(
        member_object
    ):
        raise ValueError(
            "A converted ForgeCAD bent member is required."
        )

    (
        tube,
        start_point,
        initial_direction,
        initial_bend_normal,
    ) = _resolved_bent_definition(
        member_object
    )

    first_tube, second_tube, location = (
        split_bent_tube(
            tube,
            split_point,
            start_point=start_point,
            initial_direction=initial_direction,
            initial_bend_normal=initial_bend_normal,
        )
    )

    (
        second_start,
        second_direction,
        second_normal,
        source_segment,
    ) = _second_split_frame(
        tube,
        location.straight_run_index,
        location.point,
        start_point,
        initial_direction,
        initial_bend_normal,
    )

    source_layouts = list(
        getattr(
            member_object,
            "SourceLayoutLines",
            (),
        )
    )

    if (
        len(source_layouts)
        != len(tube.straight_runs)
    ):
        raise ValueError(
            "Bent member source-layout references do not match "
            "its straight-run count."
        )

    design_nodes = list(
        _design_joint_nodes(
            member_object
        )
    )

    if (
        len(design_nodes)
        != len(tube.bends)
    ):
        raise ValueError(
            "Bent member design-joint references do not match "
            "its bend count."
        )

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
            "Bent member requires persistent StartNode and EndNode links."
        )

    start_layout_id = str(
        getattr(
            member_object,
            "StartFabricationLayoutID",
            "",
        )
    ).strip()
    end_layout_id = str(
        getattr(
            member_object,
            "EndFabricationLayoutID",
            "",
        )
    ).strip()

    if (
        not start_layout_id
        or not end_layout_id
    ):
        raise ValueError(
            "Bent member is missing endpoint fabrication identity."
        )

    from forgecad.adapters.freecad.commands.draw_member_interactive import (
        get_or_create_node,
    )

    split_node = get_or_create_node(
        document,
        location.point,
    )

    run_index = (
        location.straight_run_index
    )

    split_source_layout = (
        source_layouts[
            run_index
        ]
    )

    preserve_original_id_on_second = (
        run_index
        == len(
            tube.straight_runs
        )
        - 1
        and run_index != 0
    )

    first_split_layout, second_split_layout = (
        _create_split_source_layouts(
            document,
            split_source_layout,
            location.point,
            source_segment.start,
            source_segment.end,
            preserve_original_id_on_second=(
                preserve_original_id_on_second
            ),
        )
    )

    first_source_layouts = (
        source_layouts[:run_index]
        + [
            first_split_layout
        ]
    )

    second_source_layouts = (
        [
            second_split_layout
        ]
        + source_layouts[
            run_index + 1 :
        ]
    )

    first_design_nodes = design_nodes[
        :run_index
    ]
    second_design_nodes = design_nodes[
        run_index:
    ]

    tree = initialize_project_tree(
        document
    )
    bent_group = tree[
        "Bent Tubes"
    ]

    original_name = str(
        getattr(
            member_object,
            "TubeName",
            "",
        )
        or getattr(
            member_object,
            "Label",
            "",
        )
        or "Bent Tube"
    )

    first_object = (
        create_bent_tube_object(
            document,
            first_tube,
        )
    )
    second_object = (
        create_bent_tube_object(
            document,
            second_tube,
        )
    )

    bent_group.addObject(
        first_object
    )
    bent_group.addObject(
        second_object
    )

    _configure_bent_object(
        first_object,
        first_tube,
        tube_name=f"{original_name} A",
        start_point=start_point,
        initial_direction=initial_direction,
        initial_bend_normal=initial_bend_normal,
        start_node=start_node,
        end_node=split_node,
        source_layouts=first_source_layouts,
        design_nodes=first_design_nodes,
        start_layout_id=start_layout_id,
        end_layout_id=str(
            first_split_layout.LayoutID
        ).strip(),
    )

    _restore_split_node_position(
        split_node,
        location.point,
        first_split_layout,
        second_split_layout,
    )

    _configure_bent_object(
        second_object,
        second_tube,
        tube_name=f"{original_name} B",
        start_point=second_start,
        initial_direction=second_direction,
        initial_bend_normal=second_normal,
        start_node=split_node,
        end_node=end_node,
        source_layouts=second_source_layouts,
        design_nodes=second_design_nodes,
        start_layout_id=str(
            second_split_layout.LayoutID
        ).strip(),
        end_layout_id=end_layout_id,
    )

    _restore_split_node_position(
        split_node,
        location.point,
        first_split_layout,
        second_split_layout,
    )

    _remove_from_group(
        bent_group,
        member_object,
    )

    document.removeObject(
        member_object.Name
    )

    refresh_joint_topology(
        document
    )
    refresh_fabrication_for_document(
        document
    )
    document.recompute()

    return (
        first_split_layout,
        first_object,
        second_split_layout,
        second_object,
        split_node,
    )


def _split_straight_member_object(
    document,
    member_object,
    split_point,
):
    source_member = (
        structural_member_from_freecad_object(
            member_object
        )
    )

    first_member, second_member = (
        split_member(
            source_member,
            split_point,
        )
    )

    from forgecad.adapters.freecad.commands.draw_member_interactive import (
        get_or_create_node,
    )

    start_node = get_or_create_node(
        document,
        first_member.start,
    )
    split_node = get_or_create_node(
        document,
        first_member.end,
    )
    end_node = get_or_create_node(
        document,
        second_member.end,
    )

    first_layout, first_object = (
        create_member_between_nodes(
            document,
            start_node,
            split_node,
            profile=source_member.profile,
            material=source_member.material,
            refresh=False,
        )
    )

    second_layout, second_object = (
        create_member_between_nodes(
            document,
            split_node,
            end_node,
            profile=source_member.profile,
            material=source_member.material,
            refresh=False,
        )
    )

    remove_member_and_unused_layout(
        document,
        member_object,
    )

    refresh_joint_topology(
        document
    )
    refresh_fabrication_for_document(
        document
    )
    document.recompute()

    return (
        first_layout,
        first_object,
        second_layout,
        second_object,
        split_node,
    )


def split_member_object(
    document,
    member_object,
    split_point,
):
    """Replace one straight or converted bent ForgeCAD member with two."""

    if document is None:
        raise ValueError(
            "Split Member requires an active document."
        )

    if member_object is None:
        raise ValueError(
            "Split Member requires a ForgeCAD member."
        )

    if is_forgecad_bent_member(
        member_object
    ):
        return split_bent_member_object(
            document,
            member_object,
            split_point,
        )

    return _split_straight_member_object(
        document,
        member_object,
        split_point,
    )
