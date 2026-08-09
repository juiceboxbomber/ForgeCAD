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
        source_layout_id: str = "",
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

        proxy = TubeMemberProxy(
            obj,
            member,
            member_id,
        )

        obj.addProperty(
            "App::PropertyString",
            "SourceLayoutID",
            "ForgeCAD",
        )

        obj.SourceLayoutID = (
            source_layout_id
        )

        try:
            obj.setEditorMode(
                "SourceLayoutID",
                1,
            )
        except Exception:
            pass

        obj.ViewObject.Proxy = 0

        obj.Shape = shape
        obj.ViewObject.Visibility = True

        # SourceLayoutID now exists, so the proxy can find the
        # originating layout line and restore its persistent name.
        proxy.load_member_name_from_source(
            obj
        )

        document.recompute()

        return obj

    def render_frame(
        self,
        document,
        frame: Frame,
        source_layout_ids=None,
    ):
        """Render every member in a frame."""

        rendered_objects = []

        if source_layout_ids is None:
            source_layout_ids = [
                ""
                for _ in frame.members
            ]

        if (
            len(source_layout_ids)
            != len(frame.members)
        ):
            raise ValueError(
                "Layout identity count does not match "
                "the number of frame members."
            )

        for index, member in enumerate(
            frame.members,
            start=1,
        ):
            member_id = (
                f"M{index:03d}"
            )

            source_layout_id = (
                source_layout_ids[
                    index - 1
                ]
            )

            obj = self.render_tube(
                document,
                member,
                member_id=member_id,
                source_layout_id=source_layout_id,
            )

            rendered_objects.append(
                obj
            )

        document.recompute()

        return rendered_objects
    