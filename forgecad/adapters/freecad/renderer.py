"""Rendering of ForgeCAD objects into FreeCAD."""

import Part
import FreeCAD

from forgecad.fabrication import Frame, Member


class FrameRenderer:
    """Renders ForgeCAD objects into a FreeCAD document."""

    def render_member(self, document, member: Member):
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

    def render_tube(self, document, member: Member):
        """Render a member as a hollow round tube."""

        length = member.length

        if length <= 0:
            raise ValueError("Cannot render a zero-length member.")

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

        outer_radius = member.profile.outside_diameter / 2.0
        inner_radius = member.profile.inside_diameter / 2.0

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

        tube_shape = outer_cylinder.cut(inner_cylinder)

        obj = document.addObject(
            "Part::Feature",
            "TubeMember",
        )
        obj.Label = "Tube Member"
        obj.Shape = tube_shape

        document.recompute()

        return obj
    def render_frame(self, document, frame: Frame):
        """Render every member in a frame as a hollow tube."""

        rendered_objects = []

        for index, member in enumerate(frame.members, start=1):
            obj = self.render_tube(document, member)
            obj.Label = f"Frame Member {index}"
            rendered_objects.append(obj)

        document.recompute()

        return rendered_objects
        