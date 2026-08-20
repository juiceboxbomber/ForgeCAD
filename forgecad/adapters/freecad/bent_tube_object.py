"""Parametric FreeCAD representation of ForgeCAD bent tubes."""

import FreeCAD

from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
)
from forgecad.geometry import (
    Point3D,
    Vector3D,
)
from forgecad.services import (
    create_default_tube_library,
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

            sync_bent_tube_end_node(
                obj,
                centerline,
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
