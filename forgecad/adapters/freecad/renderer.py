"""Rendering of ForgeCAD objects into FreeCAD."""

import Part
import FreeCAD

from forgecad.fabrication import Frame, Member


class FrameRenderer:
    """Renders ForgeCAD objects into a FreeCAD document."""

    def render_member(self, document, member: Member):
        """Render a member centerline."""

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

        edge = Part.makeLine(start, end)

        obj = document.addObject(
            "Part::Feature",
            "Member",
        )

        obj.Shape = edge

        document.recompute()

        return obj

    def _add_member_properties(
        self,
        obj,
        member: Member,
        member_id: str,
    ):
        """Attach ForgeCAD fabrication properties to a rendered member."""

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
        obj.MemberID = member_id

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
        obj.MemberLength = member.length

        obj.addProperty(
            "App::PropertyString",
            "TubeProfile",
            "ForgeCAD Tube",
        )
        obj.TubeProfile = (
            f"{member.profile.outside_diameter:.3f} x "
            f"{member.profile.wall_thickness:.3f} mm"
        )

        obj.addProperty(
            "App::PropertyLength",
            "OutsideDiameter",
            "ForgeCAD Tube",
        )
        obj.OutsideDiameter = member.profile.outside_diameter

        obj.addProperty(
            "App::PropertyLength",
            "WallThickness",
            "ForgeCAD Tube",
        )
        obj.WallThickness = member.profile.wall_thickness

        obj.addProperty(
            "App::PropertyLength",
            "InsideDiameter",
            "ForgeCAD Tube",
        )
        obj.InsideDiameter = member.profile.inside_diameter

        obj.addProperty(
            "App::PropertyString",
            "Material",
            "ForgeCAD Material",
        )
        obj.Material = member.material.name

    def render_tube(
        self,
        document,
        member: Member,
        member_id: str = "",
    ):
        """Render a member as a hollow round tube."""

        length = member.length

        if length <= 0:
            raise ValueError(
                "Cannot render a zero-length member."
            )

        start = FreeCAD.Vector(
            member.start.x,
            member.start.y,
            member.start.z,
        )

        direction = FreeCAD.Vector(
            member.end.x - member.start.x,
            member.end.y - member.start.y,
            member.end.z - member.start.z,
        )

        outer_radius = (
            member.profile.outside_diameter / 2.0
        )

        inner_radius = (
            member.profile.inside_diameter / 2.0
        )

        outer_cylinder = Part.makeCylinder(
            outer_radius,
            length,
            start,
            direction,
        )

        inner_cylinder = Part.makeCylinder(
            inner_radius,
            length,
            start,
            direction,
        )

        tube_shape = outer_cylinder.cut(
            inner_cylinder
        )

        obj = document.addObject(
            "Part::Feature",
            "TubeMember",
        )

        obj.Label = "Tube Member"
        obj.Shape = tube_shape

        self._add_member_properties(
            obj,
            member,
            member_id,
        )

        document.recompute()

        return obj

    def render_frame(
        self,
        document,
        frame: Frame,
    ):
        """Render every frame member as a hollow tube."""

        rendered_objects = []

        for index, member in enumerate(
            frame.members,
            start=1,
        ):
            member_id = f"M{index:03d}"

            obj = self.render_tube(
                document,
                member,
                member_id=member_id,
            )

            obj.Label = (
                f"Frame Member {index:03d}"
            )

            rendered_objects.append(obj)

        document.recompute()

        return rendered_objects
    