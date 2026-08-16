"""Parametric FreeCAD behavior for ForgeCAD structural nodes."""

import FreeCAD
import Part


NODE_PROPERTY_GROUP = "ForgeCAD Node"
NODE_RADIUS = 6.0
POINT_PRECISION = 6


def point_key(
    vector,
    precision=POINT_PRECISION,
):
    """Return a stable coordinate key for a FreeCAD-like vector."""

    return (
        round(
            float(vector.x),
            precision,
        ),
        round(
            float(vector.y),
            precision,
        ),
        round(
            float(vector.z),
            precision,
        ),
    )


def vector_copy(
    vector,
):
    """Return a new FreeCAD vector containing the same coordinates."""

    return FreeCAD.Vector(
        float(vector.x),
        float(vector.y),
        float(vector.z),
    )


def connected_member_objects(
    document,
    node_object,
):
    """Return straight members explicitly linked to a node."""

    if (
        document is None
        or node_object is None
    ):
        return []

    connected = []

    for obj in getattr(
        document,
        "Objects",
        [],
    ):
        if (
            getattr(
                obj,
                "StartNode",
                None,
            )
            is node_object
            or getattr(
                obj,
                "EndNode",
                None,
            )
            is node_object
        ):
            connected.append(
                obj
            )

    return connected


def update_layout_object_shape(
    layout_object,
):
    """Refresh one layout object's visible line geometry."""

    proxy = getattr(
        layout_object,
        "Proxy",
        None,
    )

    if (
        proxy is not None
        and hasattr(
            proxy,
            "update_shape",
        )
    ):
        proxy.update_shape(
            layout_object
        )
        return

    if (
        hasattr(
            layout_object,
            "StartPoint",
        )
        and hasattr(
            layout_object,
            "EndPoint",
        )
    ):
        try:
            layout_object.Shape = (
                Part.makeLine(
                    layout_object.StartPoint,
                    layout_object.EndPoint,
                )
            )
        except Exception:
            pass


def sync_layout_points_for_node(
    document,
    old_position,
    new_position,
):
    """
    Move layout endpoints that occupied a node's previous position.

    Every endpoint at the old coordinate is moved. This preserves a
    shared corner when multiple layout members terminate at one node.
    Interior points of continuous through-members are intentionally
    not split or moved here.
    """

    if document is None:
        return 0

    layout_group = document.getObject(
        "ForgeCADLayout"
    )

    if layout_group is None:
        return 0

    old_key = point_key(
        old_position
    )

    changed_count = 0

    for layout_object in getattr(
        layout_group,
        "Group",
        [],
    ):
        changed = False

        if (
            hasattr(
                layout_object,
                "StartPoint",
            )
            and point_key(
                layout_object.StartPoint
            ) == old_key
        ):
            layout_object.StartPoint = (
                vector_copy(
                    new_position
                )
            )
            changed = True

        if (
            hasattr(
                layout_object,
                "EndPoint",
            )
            and point_key(
                layout_object.EndPoint
            ) == old_key
        ):
            layout_object.EndPoint = (
                vector_copy(
                    new_position
                )
            )
            changed = True

        if changed:
            update_layout_object_shape(
                layout_object
            )

            try:
                layout_object.touch()
            except Exception:
                pass

            changed_count += 1

    return changed_count


def refresh_connected_members(
    document,
    node_object,
):
    """Rebuild straight members linked to the moved node."""

    members = connected_member_objects(
        document,
        node_object,
    )

    for member_object in members:
        proxy = getattr(
            member_object,
            "Proxy",
            None,
        )

        if (
            proxy is not None
            and hasattr(
                proxy,
                "update_shape",
            )
        ):
            proxy.update_shape(
                member_object
            )

        try:
            member_object.touch()
        except Exception:
            pass

    return members


class ForgeCADNodeProxy:
    """Keep a ForgeCAD node and its connected topology synchronized."""

    def __init__(
        self,
        obj,
    ):
        self._ready = False
        self._updating = False

        obj.Proxy = self

        self._last_position = point_key(
            obj.Position
        )

        self._ready = True

    def _position_from_key(
        self,
        key,
    ):
        """Build a FreeCAD vector from a stored coordinate key."""

        return FreeCAD.Vector(
            key[0],
            key[1],
            key[2],
        )

    def _placement_position(
        self,
        obj,
    ):
        """Return the node location from Placement.Base."""

        base = obj.Placement.Base

        return FreeCAD.Vector(
            float(base.x),
            float(base.y),
            float(base.z),
        )

    def _refresh_coordinate_properties(
        self,
        obj,
        position,
    ):
        """Synchronize Position and XYZ from one authoritative point."""

        obj.Position = FreeCAD.Vector(
            float(position.x),
            float(position.y),
            float(position.z),
        )

        obj.X = float(
            position.x
        )
        obj.Y = float(
            position.y
        )
        obj.Z = float(
            position.z
        )

    def onChanged(
        self,
        obj,
        property_name,
    ):
        """Propagate Placement changes into layout and linked members."""

        if (
            not self._ready
            or self._updating
            or property_name != "Placement"
        ):
            return

        new_position = (
            self._placement_position(
                obj
            )
        )

        new_key = point_key(
            new_position
        )

        if (
            new_key
            == self._last_position
        ):
            return

        old_position = (
            self._position_from_key(
                self._last_position
            )
        )

        self._updating = True

        try:
            self._refresh_coordinate_properties(
                obj,
                new_position,
            )

            document = getattr(
                obj,
                "Document",
                None,
            )

            sync_layout_points_for_node(
                document,
                old_position,
                new_position,
            )

            refresh_connected_members(
                document,
                obj,
            )

            self._last_position = (
                new_key
            )

        finally:
            self._updating = False

    def execute(
        self,
        obj,
    ):
        """Refresh coordinate mirrors during document recompute."""

        if (
            not self._ready
            or self._updating
        ):
            return

        self._updating = True

        try:
            position = (
                self._placement_position(
                    obj
                )
            )

            self._refresh_coordinate_properties(
                obj,
                position,
            )

            self._last_position = (
                point_key(
                    position
                )
            )

        finally:
            self._updating = False

def ensure_node_proxy(
    obj,
):
    """Ensure an existing ForgeCAD node has parametric node behavior."""

    if obj is None:
        return None

    stored_position = getattr(
        obj,
        "Position",
        None,
    )

    if stored_position is None:
        stored_position = FreeCAD.Vector(
            0.0,
            0.0,
            0.0,
        )

    # Normalize the visual representation: the sphere lives at the
    # object's local origin and Placement.Base carries the node location.
    try:
        obj.Shape = Part.makeSphere(
            NODE_RADIUS
        )
    except TypeError:
        obj.Shape = Part.makeSphere(
            NODE_RADIUS,
            FreeCAD.Vector(
                0.0,
                0.0,
                0.0,
            ),
        )

    try:
        obj.Placement.Base = FreeCAD.Vector(
            float(stored_position.x),
            float(stored_position.y),
            float(stored_position.z),
        )
    except Exception:
        pass

    proxy = getattr(
        obj,
        "Proxy",
        None,
    )

    if not isinstance(
        proxy,
        ForgeCADNodeProxy,
    ):
        ForgeCADNodeProxy(
            obj
        )

    try:
        obj.ViewObject.Proxy = 0
        obj.ViewObject.Visibility = True
        obj.ViewObject.Selectable = True
    except Exception:
        pass

    # Placement is the authoritative editable location.
    try:
        obj.setEditorMode(
            "Placement",
            0,
        )
    except Exception:
        pass

    # Position and XYZ are informational mirrors.
    for property_name in (
        "NodeID",
        "Position",
        "X",
        "Y",
        "Z",
        "SourceType",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj

def create_node_object(
    document,
    point,
    node_id,
    source_type="Manual",
):
    """Create one visible, selectable, movable ForgeCAD node."""

    obj = document.addObject(
        "Part::FeaturePython",
        "ForgeCADNode",
    )

    obj.Label = node_id

    obj.addProperty(
        "App::PropertyString",
        "NodeID",
        NODE_PROPERTY_GROUP,
    )
    obj.NodeID = node_id

    obj.addProperty(
        "App::PropertyVector",
        "Position",
        NODE_PROPERTY_GROUP,
    )
    obj.Position = FreeCAD.Vector(
        float(point.x),
        float(point.y),
        float(point.z),
    )

    obj.addProperty(
        "App::PropertyFloat",
        "X",
        NODE_PROPERTY_GROUP,
    )
    obj.X = float(
        point.x
    )

    obj.addProperty(
        "App::PropertyFloat",
        "Y",
        NODE_PROPERTY_GROUP,
    )
    obj.Y = float(
        point.y
    )

    obj.addProperty(
        "App::PropertyFloat",
        "Z",
        NODE_PROPERTY_GROUP,
    )
    obj.Z = float(
        point.z
    )

    obj.addProperty(
        "App::PropertyString",
        "SourceType",
        NODE_PROPERTY_GROUP,
    )
    obj.SourceType = str(
        source_type
    )

    try:
        obj.Shape = Part.makeSphere(
            NODE_RADIUS
        )
    except TypeError:
        obj.Shape = Part.makeSphere(
            NODE_RADIUS,
            FreeCAD.Vector(
                0.0,
                0.0,
                0.0,
            ),
        )

    obj.Placement.Base = FreeCAD.Vector(
        float(point.x),
        float(point.y),
        float(point.z),
    )

    try:
        obj.ViewObject.PointSize = (
            8.0
        )
    except Exception:
        pass

    try:
        obj.ViewObject.Proxy = 0
        obj.ViewObject.Visibility = True
        obj.ViewObject.Selectable = True
    except Exception:
        pass

    ensure_node_proxy(
        obj
    )

    return obj

