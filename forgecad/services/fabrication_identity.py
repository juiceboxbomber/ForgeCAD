"""Endpoint-aware fabrication identity for ForgeCAD structural objects."""


def _clean(value) -> str:
    """Return a normalized persistent identity string."""

    return str(
        value
        if value is not None
        else ""
    ).strip()


def _xyz(point):
    """Return float XYZ values from a FreeCAD-like point/vector."""

    return (
        float(point.x),
        float(point.y),
        float(point.z),
    )


def point_key(
    point,
    precision=6,
):
    """Return a stable geometric key for one endpoint."""

    return tuple(
        round(
            value,
            precision,
        )
        for value in _xyz(
            point
        )
    )


def _linked_node_position(
    obj,
    property_name,
):
    """Return Position from a linked persistent node, when available."""

    node = getattr(
        obj,
        property_name,
        None,
    )

    if node is None:
        return None

    return getattr(
        node,
        "Position",
        None,
    )


def structural_endpoint_points(
    obj,
):
    """
    Return physical start/end endpoint points for a structural object.

    Straight generated members expose StartPoint/EndPoint.
    Converted bent members expose StartNode/EndNode links.
    """

    start_point = getattr(
        obj,
        "StartPoint",
        None,
    )
    end_point = getattr(
        obj,
        "EndPoint",
        None,
    )

    if (
        start_point is not None
        and end_point is not None
    ):
        return (
            start_point,
            end_point,
        )

    start_point = _linked_node_position(
        obj,
        "StartNode",
    )
    end_point = _linked_node_position(
        obj,
        "EndNode",
    )

    if (
        start_point is not None
        and end_point is not None
    ):
        return (
            start_point,
            end_point,
        )

    raise ValueError(
        "Object does not expose two ForgeCAD structural endpoints."
    )


def source_layout_id_from_reference(
    reference,
) -> str:
    """Return a LayoutID from a layout object or lightweight test string."""

    if reference is None:
        return ""

    if isinstance(
        reference,
        str,
    ):
        return _clean(
            reference
        )

    return _clean(
        getattr(
            reference,
            "LayoutID",
            "",
        )
    )


def bent_endpoint_layout_ids(
    obj,
):
    """
    Return the persistent source-layout identity at each bent-tube end.

    New bends store explicit endpoint identities. Older bends fall back to
    the first/last SourceLayoutLines entries so existing files remain usable
    and can be migrated without inventing a fake single SourceLayoutID.
    """

    start_id = _clean(
        getattr(
            obj,
            "StartFabricationLayoutID",
            "",
        )
    )
    end_id = _clean(
        getattr(
            obj,
            "EndFabricationLayoutID",
            "",
        )
    )

    source_layouts = tuple(
        getattr(
            obj,
            "SourceLayoutLines",
            (),
        )
        or ()
    )

    if (
        not start_id
        and source_layouts
    ):
        start_id = (
            source_layout_id_from_reference(
                source_layouts[
                    0
                ]
            )
        )

    if (
        not end_id
        and source_layouts
    ):
        end_id = (
            source_layout_id_from_reference(
                source_layouts[
                    -1
                ]
            )
        )

    return (
        start_id,
        end_id,
    )


def fabrication_layout_id_at_point(
    obj,
    point,
    precision=6,
) -> str:
    """
    Return the source layout identity represented by one structural endpoint.

    Straight members have one SourceLayoutID at both ends.
    Bent members may represent many layout segments, so the start and end
    identities are deliberately different and resolved by endpoint.
    """

    start_point, end_point = (
        structural_endpoint_points(
            obj
        )
    )

    requested = point_key(
        point,
        precision,
    )

    start_key = point_key(
        start_point,
        precision,
    )
    end_key = point_key(
        end_point,
        precision,
    )

    if requested not in (
        start_key,
        end_key,
    ):
        raise ValueError(
            "The requested point is not a structural endpoint."
        )

    straight_id = _clean(
        getattr(
            obj,
            "SourceLayoutID",
            "",
        )
    )

    if straight_id:
        return straight_id

    start_id, end_id = (
        bent_endpoint_layout_ids(
            obj
        )
    )

    if requested == start_key:
        layout_id = start_id
    else:
        layout_id = end_id

    if not layout_id:
        raise ValueError(
            "The bent tube has no fabrication identity for this endpoint."
        )

    return layout_id


def fabrication_endpoint_ids(
    obj,
):
    """Return both endpoint identities in physical start/end order."""

    start_point, end_point = (
        structural_endpoint_points(
            obj
        )
    )

    return (
        fabrication_layout_id_at_point(
            obj,
            start_point,
        ),
        fabrication_layout_id_at_point(
            obj,
            end_point,
        ),
    )

def shared_structural_endpoint(
    objects,
    precision=6,
):
    """
    Return one common structural endpoint plus endpoint-aware layout IDs.

    Straight generated members must retain SourceLayoutID. Converted bent
    tubes are the intentional exception and use persistent start/end
    fabrication identities instead.
    """

    objects = list(
        objects
        or ()
    )

    if not objects:
        raise ValueError(
            "Select one or more ForgeCAD structural tubes."
        )

    common = None
    endpoints = []

    for obj in objects:
        straight_id = _clean(
            getattr(
                obj,
                "SourceLayoutID",
                "",
            )
        )

        bent_identity = any(
            (
                _clean(
                    getattr(
                        obj,
                        "StartFabricationLayoutID",
                        "",
                    )
                ),
                _clean(
                    getattr(
                        obj,
                        "EndFabricationLayoutID",
                        "",
                    )
                ),
                bool(
                    getattr(
                        obj,
                        "SourceLayoutLines",
                        (),
                    )
                ),
            )
        )

        if (
            not straight_id
            and not bent_identity
        ):
            raise ValueError(
                "Every selected straight tube must be a generated "
                "ForgeCAD member with a SourceLayoutID; converted bent "
                "tubes must have persistent fabrication endpoint identities."
            )

        start_point, end_point = (
            structural_endpoint_points(
                obj
            )
        )

        pair = (
            (
                point_key(
                    start_point,
                    precision,
                ),
                start_point,
            ),
            (
                point_key(
                    end_point,
                    precision,
                ),
                end_point,
            ),
        )

        endpoints.append(
            pair
        )

        keys = {
            pair[0][0],
            pair[1][0],
        }

        common = (
            keys
            if common is None
            else common.intersection(
                keys
            )
        )

    if len(
        common
        or ()
    ) != 1:
        raise ValueError(
            "The selected tubes must share exactly one joint endpoint."
        )

    joint_key = next(
        iter(
            common
        )
    )

    layout_ids = []

    for obj, pair in zip(
        objects,
        endpoints,
    ):
        endpoint = next(
            point
            for key, point
            in pair
            if key == joint_key
        )

        layout_id = (
            fabrication_layout_id_at_point(
                obj,
                endpoint,
                precision=precision,
            )
        )

        if layout_id in layout_ids:
            raise ValueError(
                "Select different ForgeCAD structural tubes."
            )

        layout_ids.append(
            layout_id
        )

    return (
        joint_key,
        tuple(
            layout_ids
        ),
    )
