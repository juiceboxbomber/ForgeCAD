"""Parametric FreeCAD representation of ForgeCAD tube members."""

import FreeCAD
import Part

from forgecad.services import (
    create_default_tube_library,
)
from forgecad.adapters.freecad.member_notch import (
    build_member_shape,
    ensure_notch_properties,
)


def build_tube_shape(
    start,
    end,
    profile,
):
    """Build a hollow round tube between two FreeCAD vectors."""

    direction = FreeCAD.Vector(
        end.x - start.x,
        end.y - start.y,
        end.z - start.z,
    )

    length = direction.Length

    if length <= 0:
        raise ValueError(
            "Cannot create a zero-length ForgeCAD member."
        )

    outer_radius = (
        profile.outside_diameter
        / 2.0
    )

    inner_radius = (
        profile.inside_diameter
        / 2.0
    )

    outer_cylinder = (
        Part.makeCylinder(
            outer_radius,
            length,
            start,
            direction,
        )
    )

    inner_cylinder = (
        Part.makeCylinder(
            inner_radius,
            length,
            start,
            direction,
        )
    )

    shape = (
        outer_cylinder.cut(
            inner_cylinder
        )
    )

    return shape, length


def find_source_layout_object(obj):
    """Find the layout object that owns a generated member."""

    source_layout_id = getattr(
        obj,
        "SourceLayoutID",
        "",
    )

    if not source_layout_id:
        return None

    document = obj.Document

    if document is None:
        return None

    layout_group = (
        document.getObject(
            "ForgeCADLayout"
        )
    )

    if layout_group is None:
        return None

    for layout_object in layout_group.Group:
        layout_id = getattr(
            layout_object,
            "LayoutID",
            "",
        )

        if (
            layout_id
            == source_layout_id
        ):
            return layout_object

    return None


def ensure_profile_override_property(
    layout_object,
):
    """Ensure a layout object can store a member profile override."""

    if not hasattr(
        layout_object,
        "TubeProfileOverride",
    ):
        layout_object.addProperty(
            "App::PropertyString",
            "TubeProfileOverride",
            "ForgeCAD Layout",
        )

        layout_object.TubeProfileOverride = ""

    return layout_object


def ensure_member_name_property(
    layout_object,
):
    """Ensure a layout object can store a persistent member name."""

    if not hasattr(
        layout_object,
        "MemberName",
    ):
        layout_object.addProperty(
            "App::PropertyString",
            "MemberName",
            "ForgeCAD Layout",
        )

        layout_object.MemberName = ""

    return layout_object


class TubeMemberProxy:
    """Keep a ForgeCAD tube synchronized with editable properties."""

    def __init__(
        self,
        obj,
        member,
        member_id: str,
    ):
        self._updating = False
        self._ready = False

        obj.Proxy = self

        self._add_properties(
            obj,
            member,
            member_id,
        )

        self._ready = True

    def _add_properties(
        self,
        obj,
        member,
        member_id: str,
    ):
        """Create ForgeCAD member properties."""

        start = FreeCAD.Vector(
            member.start.x,
            member.start.y,
            member.start.z,
        )

        end = FreeCAD.Vector(
            member.end.x,
            member.end.y,
            member.end.z,
        )

        obj.addProperty(
            "App::PropertyString",
            "MemberID",
            "ForgeCAD",
        )
        obj.MemberID = (
            member_id
        )

        obj.addProperty(
            "App::PropertyString",
            "MemberName",
            "ForgeCAD",
        )
        obj.MemberName = ""

        obj.addProperty(
            "App::PropertyVector",
            "StartPoint",
            "ForgeCAD Geometry",
        )
        obj.StartPoint = start

        obj.addProperty(
            "App::PropertyVector",
            "EndPoint",
            "ForgeCAD Geometry",
        )
        obj.EndPoint = end

        obj.addProperty(
            "App::PropertyLength",
            "MemberLength",
            "ForgeCAD Geometry",
        )
        obj.MemberLength = (
            member.length
        )

        obj.addProperty(
            "App::PropertyEnumeration",
            "TubeProfile",
            "ForgeCAD Tube",
        )

        library = (
            create_default_tube_library()
        )

        obj.TubeProfile = list(
            library.names
        )

        obj.TubeProfile = (
            self._profile_name_for_member(
                member
            )
        )

        obj.addProperty(
            "App::PropertyLength",
            "OutsideDiameter",
            "ForgeCAD Tube",
        )

        obj.addProperty(
            "App::PropertyLength",
            "WallThickness",
            "ForgeCAD Tube",
        )

        obj.addProperty(
            "App::PropertyLength",
            "InsideDiameter",
            "ForgeCAD Tube",
        )

        obj.addProperty(
            "App::PropertyString",
            "Material",
            "ForgeCAD Material",
        )

        obj.Material = (
            member.material.name
        )

        self._update_profile_properties(
            obj,
            member.profile,
        )

        # Every ForgeCAD member now knows whether it should
        # regenerate as a plain tube or as a coped tube.
        ensure_notch_properties(
            obj
        )

        for property_name in (
            "MemberID",
            "StartPoint",
            "EndPoint",
            "MemberLength",
            "OutsideDiameter",
            "WallThickness",
            "InsideDiameter",
            "Material",
        ):
            try:
                obj.setEditorMode(
                    property_name,
                    1,
                )
            except Exception:
                pass

    def _profile_name_for_member(
        self,
        member,
    ):
        """Return the library name matching the member profile."""

        library = (
            create_default_tube_library()
        )

        for name in library.names:
            if (
                library.get(name)
                == member.profile
            ):
                return name

        return library.active_name

    def _selected_profile(
        self,
        obj,
    ):
        """Return the selected profile."""

        library = (
            create_default_tube_library()
        )

        return library.get(
            str(obj.TubeProfile)
        )

    def _update_profile_properties(
        self,
        obj,
        profile,
    ):
        """Update tube information properties."""

        obj.OutsideDiameter = (
            profile.outside_diameter
        )

        obj.WallThickness = (
            profile.wall_thickness
        )

        obj.InsideDiameter = (
            profile.inside_diameter
        )

    def _store_profile_override(
        self,
        obj,
    ):
        """Store the selected profile on the source layout line."""

        source_object = (
            find_source_layout_object(
                obj
            )
        )

        if source_object is None:
            return

        ensure_profile_override_property(
            source_object
        )

        source_object.TubeProfileOverride = (
            str(
                obj.TubeProfile
            )
        )

    def _store_member_name(
        self,
        obj,
    ):
        """Store the member name on the source layout line."""

        source_object = (
            find_source_layout_object(
                obj
            )
        )

        if source_object is None:
            return

        ensure_member_name_property(
            source_object
        )

        source_object.MemberName = (
            str(
                obj.MemberName
            ).strip()
        )

    def _update_label(
        self,
        obj,
    ):
        """Update the tree label from the member ID and name."""

        member_id = str(
            obj.MemberID
        ).strip()

        member_name = str(
            obj.MemberName
        ).strip()

        if member_name:
            obj.Label = (
                f"{member_id} - "
                f"{member_name}"
            )
        else:
            obj.Label = (
                f"Frame Member "
                f"{member_id}"
            )

    def load_member_name_from_source(
        self,
        obj,
    ):
        """Load a persisted member name from the source layout line."""

        source_object = (
            find_source_layout_object(
                obj
            )
        )

        if source_object is None:
            self._update_label(
                obj
            )
            return

        ensure_member_name_property(
            source_object
        )

        obj.MemberName = str(
            source_object.MemberName
        ).strip()

        self._update_label(
            obj
        )

    def update_shape(
        self,
        obj,
    ):
        """Regenerate the plain or coped tube geometry."""

        if self._updating:
            return

        self._updating = True

        try:
            profile = (
                self._selected_profile(
                    obj
                )
            )

            shape, length = (
                build_member_shape(
                    obj,
                    profile,
                    build_tube_shape,
                )
            )

            obj.Shape = shape

            obj.MemberLength = (
                length
            )

            self._update_profile_properties(
                obj,
                profile,
            )

        finally:
            self._updating = False

    def onChanged(
        self,
        obj,
        property_name,
    ):
        """Regenerate geometry and persist editable changes."""

        if not self._ready:
            return

        if property_name == "TubeProfile":
            self.update_shape(
                obj
            )

            self._store_profile_override(
                obj
            )

        elif property_name == "MemberName":
            self._store_member_name(
                obj
            )

            self._update_label(
                obj
            )

    def execute(
        self,
        obj,
    ):
        """Regenerate geometry during document recompute."""

        if self._ready:
            self.update_shape(
                obj
            )

            self._update_label(
                obj
            )
            