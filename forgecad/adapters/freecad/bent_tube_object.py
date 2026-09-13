"""Parametric FreeCAD representation of ForgeCAD bent tubes."""

import FreeCAD

from forgecad.fabrication import (
    Bend,
    BentTube,
    Joint,
    Material,
    Member,
    Node,
    StraightRun,
)
from forgecad.geometry import (
    Point3D,
    Vector3D,
)
from forgecad.services import (
    create_default_tube_library,
)
from forgecad.services.joint_bend import (
    bend_specification_from_joint,
)
from forgecad.services.multi_joint_bend import (
    build_multi_joint_bent_tube,
)
from forgecad.adapters.freecad.bent_tube_geometry import (
    build_bent_tube_shape,
)


def _quantity_value(value) -> float:
    """Return a numeric value from a FreeCAD quantity or test double."""

    return float(
        getattr(
            value,
            "Value",
            value,
        )
    )


def _vector_to_point(vector) -> Point3D:
    """Convert a FreeCAD vector-like object to Point3D."""

    return Point3D(
        float(vector.x),
        float(vector.y),
        float(vector.z),
    )


def _vector_to_direction(vector) -> Vector3D:
    """Convert a FreeCAD vector-like object to Vector3D."""

    return Vector3D(
        float(vector.x),
        float(vector.y),
        float(vector.z),
    )


def ensure_bent_tube_node_links(
    obj,
    start_node,
    end_node,
):
    """Ensure a bent tube stores persistent endpoint-node links."""

    if not hasattr(
        obj,
        "StartNode",
    ):
        obj.addProperty(
            "App::PropertyLink",
            "StartNode",
            "ForgeCAD Topology",
        )

    if not hasattr(
        obj,
        "EndNode",
    ):
        obj.addProperty(
            "App::PropertyLink",
            "EndNode",
            "ForgeCAD Topology",
        )

    obj.StartNode = start_node
    obj.EndNode = end_node

    return obj


def ensure_bent_tube_design_joint_links(
    obj,
    design_joint_nodes=(),
):
    """
    Ensure numbered persistent design-joint links exist in path order.

    Existing one-bend documents may still use the legacy DesignJointNode
    property. When present, migrate that link to DesignJointNode1 while
    leaving the legacy property untouched for backward compatibility.
    """

    if obj is None:
        raise ValueError(
            "A bent-tube object is required."
        )

    requested_nodes = list(
        design_joint_nodes
    )

    legacy_joint = getattr(
        obj,
        "DesignJointNode",
        None,
    )

    if (
        legacy_joint is not None
        and not requested_nodes
    ):
        requested_nodes.insert(
            0,
            legacy_joint,
        )

    for index, node_object in enumerate(
        requested_nodes,
        start=1,
    ):
        property_name = (
            f"DesignJointNode{index}"
        )

        if not hasattr(
            obj,
            property_name,
        ):
            obj.addProperty(
                "App::PropertyLink",
                property_name,
                "ForgeCAD Topology",
            )

        setattr(
            obj,
            property_name,
            node_object,
        )

        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj


def sync_bent_tube_start_from_node(
    obj,
):
    """Synchronize bent-tube StartPoint from its linked StartNode."""

    start_node = getattr(
        obj,
        "StartNode",
        None,
    )

    if (
        start_node is None
        or not hasattr(
            start_node,
            "Position",
        )
    ):
        return False

    position = start_node.Position

    obj.StartPoint = FreeCAD.Vector(
        float(position.x),
        float(position.y),
        float(position.z),
    )

    return True


def sync_bent_tube_end_node(
    obj,
    centerline,
):
    """Move the linked EndNode to the solved bent-tube endpoint."""

    end_node = getattr(
        obj,
        "EndNode",
        None,
    )

    if (
        end_node is None
        or centerline is None
    ):
        return False

    end_point = centerline.end_point

    new_position = FreeCAD.Vector(
        float(end_point.x),
        float(end_point.y),
        float(end_point.z),
    )

    if hasattr(
        end_node,
        "Placement",
    ):
        try:
            end_node.Placement.Base = (
                new_position
            )
            return True
        except Exception:
            pass

    if hasattr(
        end_node,
        "Position",
    ):
        end_node.Position = (
            new_position
        )
        return True

    return False


def _node_from_link(
    node_object,
) -> Node:
    """Return a fabrication Node from a linked FreeCAD node object."""

    if (
        node_object is None
        or not hasattr(
            node_object,
            "Position",
        )
    ):
        raise ValueError(
            "Joint-derived bend is missing a required linked node."
        )

    position = node_object.Position

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


class BentTubeProxy:
    """Keep one ForgeCAD bent tube synchronized with editable properties."""

    def __init__(
        self,
        obj,
        tube: BentTube,
    ):
        self._updating = False
        self._ready = False
        self._geometry_dirty = True
        self._last_joint_geometry = None

        obj.Proxy = self

        self._add_properties(
            obj,
            tube,
        )

        self._ready = True

    def _add_properties(
        self,
        obj,
        tube: BentTube,
    ):
        """Create the first parametric bent-tube properties."""

        obj.addProperty(
            "App::PropertyString",
            "TubeName",
            "ForgeCAD",
        )
        obj.TubeName = ""

        obj.addProperty(
            "App::PropertyVector",
            "StartPoint",
            "ForgeCAD Geometry",
        )
        obj.StartPoint = FreeCAD.Vector(
            0.0,
            0.0,
            0.0,
        )

        obj.addProperty(
            "App::PropertyVector",
            "InitialDirection",
            "ForgeCAD Geometry",
        )
        obj.InitialDirection = FreeCAD.Vector(
            1.0,
            0.0,
            0.0,
        )

        obj.addProperty(
            "App::PropertyVector",
            "InitialBendNormal",
            "ForgeCAD Geometry",
        )
        obj.InitialBendNormal = FreeCAD.Vector(
            0.0,
            0.0,
            1.0,
        )

        obj.addProperty(
            "App::PropertyEnumeration",
            "TubeProfile",
            "ForgeCAD Tube",
        )

        library = create_default_tube_library()

        obj.TubeProfile = list(
            library.names
        )
        obj.TubeProfile = (
            self._profile_name_for_tube(
                tube
            )
        )

        obj.addProperty(
            "App::PropertyString",
            "Material",
            "ForgeCAD Material",
        )
        obj.Material = (
            tube.material.name
        )

        obj.addProperty(
            "App::PropertyInteger",
            "BendCount",
            "ForgeCAD Bending",
        )

        obj.addProperty(
            "App::PropertyLength",
            "DevelopedLength",
            "ForgeCAD Bending",
        )

        for index, run in enumerate(
            tube.straight_runs,
            start=1,
        ):
            property_name = (
                f"Run{index}Length"
            )

            obj.addProperty(
                "App::PropertyLength",
                property_name,
                "ForgeCAD Path",
            )

            setattr(
                obj,
                property_name,
                run.length_mm,
            )

        for index, bend in enumerate(
            tube.bends,
            start=1,
        ):
            angle_name = (
                f"Bend{index}Angle"
            )
            radius_name = (
                f"Bend{index}Radius"
            )
            rotation_name = (
                f"Bend{index}Rotation"
            )

            obj.addProperty(
                "App::PropertyAngle",
                angle_name,
                "ForgeCAD Path",
            )
            obj.addProperty(
                "App::PropertyLength",
                radius_name,
                "ForgeCAD Path",
            )
            obj.addProperty(
                "App::PropertyAngle",
                rotation_name,
                "ForgeCAD Path",
            )

            setattr(
                obj,
                angle_name,
                bend.angle_degrees,
            )
            setattr(
                obj,
                radius_name,
                bend.centerline_radius,
            )
            setattr(
                obj,
                rotation_name,
                bend.rotation_degrees,
            )

        self._bend_count = (
            tube.bend_count
        )

        self._update_summary_properties(
            obj,
            tube,
        )

        for property_name in (
            "Material",
            "BendCount",
            "DevelopedLength",
        ):
            try:
                obj.setEditorMode(
                    property_name,
                    1,
                )
            except Exception:
                pass

    def replace_tube_definition(
        self,
        obj,
        tube: BentTube,
    ):
        """
        Replace the parametric path definition while preserving object identity.

        Additional RunNLength and BendN* properties are created as needed.
        Existing properties are reused so a one-bend FreeCAD object can grow
        into a multi-bend object without replacing the document object.
        """

        if not isinstance(
            tube,
            BentTube,
        ):
            raise TypeError(
                "replace_tube_definition requires a BentTube."
            )

        previous_ready = self._ready
        self._ready = False

        try:
            required_run_count = len(
                tube.straight_runs
            )

            required_bend_count = len(
                tube.bends
            )

            for index, run in enumerate(
                tube.straight_runs,
                start=1,
            ):
                property_name = (
                    f"Run{index}Length"
                )

                if not hasattr(
                    obj,
                    property_name,
                ):
                    obj.addProperty(
                        "App::PropertyLength",
                        property_name,
                        "ForgeCAD Path",
                    )

                setattr(
                    obj,
                    property_name,
                    run.length_mm,
                )

            for index, bend in enumerate(
                tube.bends,
                start=1,
            ):
                angle_name = (
                    f"Bend{index}Angle"
                )

                radius_name = (
                    f"Bend{index}Radius"
                )

                rotation_name = (
                    f"Bend{index}Rotation"
                )

                if not hasattr(
                    obj,
                    angle_name,
                ):
                    obj.addProperty(
                        "App::PropertyAngle",
                        angle_name,
                        "ForgeCAD Path",
                    )

                if not hasattr(
                    obj,
                    radius_name,
                ):
                    obj.addProperty(
                        "App::PropertyLength",
                        radius_name,
                        "ForgeCAD Path",
                    )

                if not hasattr(
                    obj,
                    rotation_name,
                ):
                    obj.addProperty(
                        "App::PropertyAngle",
                        rotation_name,
                        "ForgeCAD Path",
                    )

                setattr(
                    obj,
                    angle_name,
                    bend.angle_degrees,
                )

                setattr(
                    obj,
                    radius_name,
                    bend.centerline_radius,
                )

                setattr(
                    obj,
                    rotation_name,
                    bend.rotation_degrees,
                )

            # Keep the document's profile/material metadata synchronized
            # with the replacement domain definition.
            obj.TubeProfile = (
                self._profile_name_for_tube(
                    tube
                )
            )

            obj.Material = (
                tube.material.name
            )

            self._bend_count = (
                required_bend_count
            )

            self._update_summary_properties(
                obj,
                tube,
            )

            # Any properties left over from a future path shrink are ignored
            # because _tube_from_properties reads only through _bend_count.
            # Current joint-to-bend extension only grows the path.
            _ = required_run_count

            self._geometry_dirty = True
            self._last_joint_geometry = None

        finally:
            self._ready = previous_ready

        self.update_shape(
            obj
        )

        return obj

    def _profile_name_for_tube(
        self,
        tube,
    ):
        """Return the default-library name matching the tube profile."""

        library = create_default_tube_library()

        for name in library.names:
            if (
                library.get(name)
                == tube.profile
            ):
                return name

        return library.active_name

    def _selected_profile(
        self,
        obj,
    ):
        """Return the currently selected tube profile."""

        library = create_default_tube_library()

        return library.get(
            str(obj.TubeProfile)
        )

    def _material(
        self,
        obj,
    ) -> Material:
        """Rebuild material metadata retained by the document object."""

        return Material(
            name=str(
                obj.Material
            ),
            density=7850.0,
            yield_strength=350.0,
        )

    def _tube_from_properties(
        self,
        obj,
    ) -> BentTube:
        """Rebuild the fabrication BentTube from editable properties."""

        runs = tuple(
            StraightRun(
                _quantity_value(
                    getattr(
                        obj,
                        f"Run{index}Length",
                    )
                )
            )
            for index in range(
                1,
                self._bend_count + 2,
            )
        )

        bends = tuple(
            Bend(
                angle_degrees=_quantity_value(
                    getattr(
                        obj,
                        f"Bend{index}Angle",
                    )
                ),
                centerline_radius=_quantity_value(
                    getattr(
                        obj,
                        f"Bend{index}Radius",
                    )
                ),
                rotation_degrees=_quantity_value(
                    getattr(
                        obj,
                        f"Bend{index}Rotation",
                    )
                ),
            )
            for index in range(
                1,
                self._bend_count + 1,
            )
        )

        return BentTube(
            straight_runs=runs,
            bends=bends,
            profile=self._selected_profile(
                obj
            ),
            material=self._material(
                obj
            ),
        )

    def _update_summary_properties(
        self,
        obj,
        tube,
    ):
        """Update calculated bent-tube properties."""

        obj.BendCount = (
            tube.bend_count
        )
        obj.DevelopedLength = (
            tube.developed_length
        )

    def _update_label(
        self,
        obj,
    ):
        """Update the tree label."""

        name = str(
            obj.TubeName
        ).strip()

        if name:
            obj.Label = name
        else:
            obj.Label = (
                "Bent Tube"
            )

    @staticmethod
    def _design_joint_link_objects(
        obj,
    ):
        """Return numbered design-joint links in start-to-end path order."""

        joints = []
        index = 1

        while True:
            property_name = (
                f"DesignJointNode{index}"
            )

            if not hasattr(
                obj,
                property_name,
            ):
                break

            node_object = getattr(
                obj,
                property_name,
                None,
            )

            if node_object is not None:
                joints.append(
                    node_object
                )

            index += 1

        return tuple(
            joints
        )

    def _is_multi_joint_derived_bend(
        self,
        obj,
    ) -> bool:
        """Return True when a multi-bend tube is controlled by design joints."""

        start_node = getattr(
            obj,
            "StartNode",
            None,
        )

        end_node = getattr(
            obj,
            "EndNode",
            None,
        )

        bend_count = int(
            _quantity_value(
                getattr(
                    obj,
                    "BendCount",
                    0,
                )
            )
        )

        if (
            start_node is None
            or end_node is None
            or bend_count < 2
        ):
            return False

        joint_nodes = (
            self._design_joint_link_objects(
                obj
            )
        )

        if len(
            joint_nodes
        ) != bend_count:
            return False

        return all(
            hasattr(
                obj,
                f"Bend{index}Radius",
            )
            for index in range(
                1,
                bend_count + 1,
            )
        )

    def _refresh_multi_joint_derived_path(
        self,
        obj,
    ) -> bool:
        """
        Recalculate a multi-bend tube from authoritative linked design nodes.

        StartNode, DesignJointNode1..N, and EndNode define the theoretical
        design path. Existing BendNRadius values remain user-controlled.
        Straight runs, bend angles, and bend rotations are recalculated from
        that path so moving any design node updates the complete tube.
        """

        if not self._is_multi_joint_derived_bend(
            obj
        ):
            return False

        joint_objects = (
            self._design_joint_link_objects(
                obj
            )
        )

        node_objects = (
            getattr(
                obj,
                "StartNode",
            ),
            *joint_objects,
            getattr(
                obj,
                "EndNode",
            ),
        )

        nodes = tuple(
            _node_from_link(
                node_object
            )
            for node_object in node_objects
        )

        bend_count = len(
            joint_objects
        )

        radii = tuple(
            _quantity_value(
                getattr(
                    obj,
                    f"Bend{index}Radius",
                )
            )
            for index in range(
                1,
                bend_count + 1,
            )
        )

        tube = (
            build_multi_joint_bent_tube(
                nodes=nodes,
                centerline_radii_mm=radii,
                profile=self._selected_profile(
                    obj
                ),
                material=self._material(
                    obj
                ),
            )
        )

        for index, run in enumerate(
            tube.straight_runs,
            start=1,
        ):
            setattr(
                obj,
                f"Run{index}Length",
                run.length_mm,
            )

        for index, bend in enumerate(
            tube.bends,
            start=1,
        ):
            setattr(
                obj,
                f"Bend{index}Angle",
                bend.angle_degrees,
            )

            setattr(
                obj,
                f"Bend{index}Rotation",
                bend.rotation_degrees,
            )

        first_direction = Vector3D(
            nodes[
                1
            ].x
            - nodes[
                0
            ].x,
            nodes[
                1
            ].y
            - nodes[
                0
            ].y,
            nodes[
                1
            ].z
            - nodes[
                0
            ].z,
        ).normalized()

        first_outgoing = Vector3D(
            nodes[
                2
            ].x
            - nodes[
                1
            ].x,
            nodes[
                2
            ].y
            - nodes[
                1
            ].y,
            nodes[
                2
            ].z
            - nodes[
                1
            ].z,
        ).normalized()

        first_normal = first_direction.cross(
            first_outgoing
        )

        if first_normal.magnitude <= 1e-12:
            raise ValueError(
                "Cannot determine the first bend plane from collinear nodes."
            )

        first_normal = (
            first_normal.normalized()
        )

        obj.StartPoint = FreeCAD.Vector(
            float(
                nodes[
                    0
                ].x
            ),
            float(
                nodes[
                    0
                ].y
            ),
            float(
                nodes[
                    0
                ].z
            ),
        )

        obj.InitialDirection = FreeCAD.Vector(
            float(
                first_direction.x
            ),
            float(
                first_direction.y
            ),
            float(
                first_direction.z
            ),
        )

        obj.InitialBendNormal = FreeCAD.Vector(
            float(
                first_normal.x
            ),
            float(
                first_normal.y
            ),
            float(
                first_normal.z
            ),
        )

        return True

    def _is_joint_derived_bend(
        self,
        obj,
    ) -> bool:
        """Return True when a bent tube is controlled by a design joint."""

        design_joint = getattr(
            obj,
            "DesignJointNode",
            None,
        )

        start_node = getattr(
            obj,
            "StartNode",
            None,
        )

        end_node = getattr(
            obj,
            "EndNode",
            None,
        )

        if (
            design_joint is None
            or start_node is None
            or end_node is None
            or not hasattr(
                obj,
                "Bend1Radius",
            )
        ):
            return False

        bend_count = int(
            _quantity_value(
                getattr(
                    obj,
                    "BendCount",
                    0,
                )
            )
        )

        return bend_count == 1

    def _refresh_joint_derived_path(
        self,
        obj,
    ) -> bool:
        """
        Recalculate a converted joint bend from fixed structural nodes.

        StartNode, DesignJointNode, and EndNode are authoritative. Changing
        CLR changes tangent setback and straight-run lengths rather than
        moving the frame endpoints.
        """

        if not self._is_joint_derived_bend(
            obj
        ):
            return False

        start_node = _node_from_link(
            obj.StartNode
        )

        design_joint_node = _node_from_link(
            obj.DesignJointNode
        )

        end_node = _node_from_link(
            obj.EndNode
        )

        profile = self._selected_profile(
            obj
        )

        material = self._material(
            obj
        )

        first_member = Member(
            start=start_node,
            end=design_joint_node,
            profile=profile,
            material=material,
        )

        second_member = Member(
            start=design_joint_node,
            end=end_node,
            profile=profile,
            material=material,
        )

        joint = Joint(
            node=design_joint_node,
            members=[
                first_member,
                second_member,
            ],
        )

        specification = (
            bend_specification_from_joint(
                joint,
                centerline_radius_mm=(
                    _quantity_value(
                        obj.Bend1Radius
                    )
                ),
                name=(
                    str(
                        getattr(
                            obj,
                            "TubeName",
                            "",
                        )
                    ).strip()
                    or "Bent Joint"
                ),
            )
        )

        obj.Run1Length = (
            specification.tube
            .straight_runs[
                0
            ]
            .length_mm
        )

        obj.Run2Length = (
            specification.tube
            .straight_runs[
                1
            ]
            .length_mm
        )

        obj.Bend1Angle = (
            specification.bend_angle_degrees
        )

        obj.Bend1Rotation = 0.0

        obj.StartPoint = FreeCAD.Vector(
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

        obj.InitialDirection = FreeCAD.Vector(
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

        obj.InitialBendNormal = FreeCAD.Vector(
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

        return True

    @staticmethod
    def _linked_node_position_key(
        node_object,
    ):
        """Return a stable XYZ key for one linked node object."""

        if (
            node_object is None
            or not hasattr(
                node_object,
                "Position",
            )
        ):
            return None

        position = node_object.Position

        return (
            round(
                float(
                    position.x
                ),
                7,
            ),
            round(
                float(
                    position.y
                ),
                7,
            ),
            round(
                float(
                    position.z
                ),
                7,
            ),
        )

    def _joint_geometry_signature(
        self,
        obj,
    ):
        """Return authoritative linked geometry for a joint-derived bent tube."""

        if self._is_multi_joint_derived_bend(
            obj
        ):
            node_objects = (
                getattr(
                    obj,
                    "StartNode",
                    None,
                ),
                *self._design_joint_link_objects(
                    obj
                ),
                getattr(
                    obj,
                    "EndNode",
                    None,
                ),
            )

        elif self._is_joint_derived_bend(
            obj
        ):
            node_objects = (
                getattr(
                    obj,
                    "StartNode",
                    None,
                ),
                getattr(
                    obj,
                    "DesignJointNode",
                    None,
                ),
                getattr(
                    obj,
                    "EndNode",
                    None,
                ),
            )

        else:
            return None

        keys = tuple(
            self._linked_node_position_key(
                node_object
            )
            for node_object in node_objects
        )

        if any(
            key is None
            for key in keys
        ):
            return None

        return keys

    def _joint_link_geometry_changed(
        self,
        obj,
    ) -> bool:
        """Return True when a joint-derived bend's controlling nodes moved."""

        signature = (
            self._joint_geometry_signature(
                obj
            )
        )

        if signature is None:
            return False

        return (
            signature
            != self._last_joint_geometry
        )

    def _linked_start_node_changed(
        self,
        obj,
    ) -> bool:
        """Return True when the linked StartNode no longer matches StartPoint."""

        start_node = getattr(
            obj,
            "StartNode",
            None,
        )

        if (
            start_node is None
            or not hasattr(
                start_node,
                "Position",
            )
        ):
            return False

        node_position = (
            start_node.Position
        )

        start_point = (
            obj.StartPoint
        )

        tolerance = 1e-7

        return (
            abs(
                float(node_position.x)
                - float(start_point.x)
            )
            > tolerance
            or abs(
                float(node_position.y)
                - float(start_point.y)
            )
            > tolerance
            or abs(
                float(node_position.z)
                - float(start_point.z)
            )
            > tolerance
        )

    def mark_geometry_dirty(
        self,
    ):
        """Mark the bent-tube solid for rebuilding on recompute."""

        self._geometry_dirty = True

    def update_shape(
        self,
        obj,
    ):
        """Rebuild the continuous bent-tube solid."""

        if self._updating:
            return

        self._updating = True

        try:
            sync_bent_tube_start_from_node(
                obj
            )

            multi_joint_derived = (
                self._refresh_multi_joint_derived_path(
                    obj
                )
            )

            joint_derived = (
                multi_joint_derived
                or self._refresh_joint_derived_path(
                    obj
                )
            )

            tube = self._tube_from_properties(
                obj
            )

            shape, centerline = (
                build_bent_tube_shape(
                    tube,
                    start_point=_vector_to_point(
                        obj.StartPoint
                    ),
                    initial_direction=_vector_to_direction(
                        obj.InitialDirection
                    ),
                    initial_bend_normal=_vector_to_direction(
                        obj.InitialBendNormal
                    ),
                )
            )

            obj.Shape = shape

            self._update_summary_properties(
                obj,
                tube,
            )

            if not joint_derived:
                sync_bent_tube_end_node(
                    obj,
                    centerline,
                )

                self._last_joint_geometry = None

            else:
                self._last_joint_geometry = (
                    self._joint_geometry_signature(
                        obj
                    )
                )

            self._geometry_dirty = False

        finally:
            self._updating = False

    def onChanged(
        self,
        obj,
        property_name,
    ):
        """Regenerate geometry after editable path changes."""

        if not self._ready:
            return

        if property_name == "TubeName":
            self._update_label(
                obj
            )
            return

        editable_geometry = {
            "StartPoint",
            "InitialDirection",
            "InitialBendNormal",
            "TubeProfile",
        }

        editable_geometry.update(
            f"Run{index}Length"
            for index in range(
                1,
                self._bend_count + 2,
            )
        )

        for index in range(
            1,
            self._bend_count + 1,
        ):
            editable_geometry.update(
                {
                    f"Bend{index}Angle",
                    f"Bend{index}Radius",
                    f"Bend{index}Rotation",
                }
            )

        if property_name in editable_geometry:
            self.mark_geometry_dirty()

            self.update_shape(
                obj
            )

    def execute(
        self,
        obj,
    ):
        """Regenerate geometry during document recompute."""

        if not self._ready:
            return

        if (
            self._geometry_dirty
            or self._linked_start_node_changed(
                obj
            )
            or self._joint_link_geometry_changed(
                obj
            )
        ):
            self.update_shape(
                obj
            )

        self._update_label(
            obj
        )


def create_bent_tube_object(
    document,
    tube: BentTube,
    name: str = "ForgeCADBentTube",
):
    """Create one parametric ForgeCAD bent-tube document object."""

    obj = document.addObject(
        "Part::FeaturePython",
        name,
    )

    BentTubeProxy(
        obj,
        tube,
    )

    # Use FreeCAD's default Shape view provider for this
    # FeaturePython object. Without this, the object can exist
    # in the tree with a valid Shape but have no visible display.
    obj.ViewObject.Proxy = 0
    obj.ViewObject.Visibility = True

    # Use finer tessellation for curved tube geometry.
    # This changes display quality only; the underlying
    # circular bend geometry remains exact.
    try:
        obj.ViewObject.Deviation = 0.05
        obj.ViewObject.AngularDeflection = 5.0
    except Exception:
        pass

    obj.Proxy.update_shape(
        obj
    )
    obj.Proxy._update_label(
        obj
    )

    document.recompute()

    return obj
