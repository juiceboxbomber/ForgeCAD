"""Rendering of ForgeCAD objects into FreeCAD."""

import Part
import FreeCAD

from forgecad.fabrication import Member


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
    