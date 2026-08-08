"""Rendering of ForgeCAD objects into FreeCAD."""

import Part
import FreeCAD

from forgecad.fabrication import Frame, Member
from forgecad.adapters.freecad.member_object import (
    TubeMemberProxy,
    build_tube_shape,
)


class FrameRenderer:
    """Renders ForgeCAD objects into a FreeCAD document."""

    def render_member(
        self,
        document,
        member: Member,
    ):
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

        obj = document.addObject(
            "Part::Feature",
            "Member",
        )

        obj.Shape = Part.makeLine(
            start,
            end,
        )

        document.recompute()

        return obj

    def render_tube(
        self,
        document,
        member: Member,
        member_id: str = "",
    ):
        """Render an editable hollow ForgeCAD tube."""

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

        shape, _ = build_tube_shape(
            start,
            end,
            member.profile,
        )

        obj = document.addObject(
            "Part::FeaturePython",
            "TubeMember",
        )

        obj.Label = "Tube Member"

        TubeMemberProxy(
            obj,
            member,
            member_id,
        )

        # Important for simple FeaturePython shape objects.
        obj.ViewObject.Proxy = 0

        obj.Shape = shape

        obj.ViewObject.Visibility = True

        document.recompute()

        return obj

    def render_frame(
        self,
        document,
        frame: Frame,
    ):
        """Render every member in a frame."""

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

            rendered_objects.append(
                obj
            )

        document.recompute()

        return rendered_objects
    