"""Rendering of ForgeCAD objects into FreeCAD."""

import Part
import FreeCAD

from forgecad.fabrication import (
    Frame,
    Member,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
)
from forgecad.services import (
    detect_joints,
    member_other_node,
    notch_specifications_for_joint,
)
from forgecad.services.notch_analysis import (
    cope_specifications_for_treatment,
)
from forgecad.adapters.freecad.member_object import (
    TubeMemberProxy,
    build_tube_shape,
)
from forgecad.adapters.freecad.member_notch import (
    clear_notch,
    configure_notch,
)


def node_vector(
    node,
):
    """Convert a ForgeCAD domain node to a FreeCAD vector."""

    return FreeCAD.Vector(
        node.x,
        node.y,
        node.z,
    )


# ---------------------------------------------------------
# Legacy automatic-notch helpers
#
# Keep these available while the rest of ForgeCAD migrates
# from NotchSpecification to generalized CopeSpecification.
# ---------------------------------------------------------

def through_axis_for_specification(
    specification,
):
    """
    Return a continuous FreeCAD axis for a legacy notch cutter.

    The two through members meet at the joint. Their opposite
    endpoints define the complete through-tube centerline.
    """

    first_member = (
        specification.through_members[
            0
        ]
    )

    second_member = (
        specification.through_members[
            1
        ]
    )

    first_outer_node = (
        member_other_node(
            first_member,
            specification.joint.node,
        )
    )

    second_outer_node = (
        member_other_node(
            second_member,
            specification.joint.node,
        )
    )

    return (
        node_vector(
            first_outer_node
        ),
        node_vector(
            second_outer_node
        ),
    )


def automatic_notch_specifications(
    frame,
):
    """Return legacy automatic notch specifications for a frame."""

    specifications = []

    for joint in detect_joints(
        frame
    ):
        specifications.extend(
            notch_specifications_for_joint(
                joint
            )
        )

    return tuple(
        specifications
    )


def configure_automatic_notches(
    frame,
    rendered_objects,
):
    """
    Apply legacy automatic notch information to rendered members.

    This remains available for compatibility while the renderer
    itself uses the generalized cope path.
    """

    if (
        len(rendered_objects)
        != len(frame.members)
    ):
        raise ValueError(
            "Rendered member count does not match "
            "the domain frame."
        )

    object_by_member_identity = {
        id(member): obj
        for member, obj in zip(
            frame.members,
            rendered_objects,
        )
    }

    for obj in rendered_objects:
        clear_notch(
            obj
        )

    configured_member_ids = set()

    for specification in (
        automatic_notch_specifications(
            frame
        )
    ):
        branch_key = id(
            specification.branch_member
        )

        branch_object = (
            object_by_member_identity.get(
                branch_key
            )
        )

        if branch_object is None:
            continue

        if (
            branch_key
            in configured_member_ids
        ):
            raise ValueError(
                "Automatic notch generation currently "
                "supports one notched end per member."
            )

        through_start, through_end = (
            through_axis_for_specification(
                specification
            )
        )

        configure_notch(
            branch_object,
            through_start,
            through_end,
            specification.through_outside_diameter,
        )

        configured_member_ids.add(
            branch_key
        )

    return rendered_objects


# ---------------------------------------------------------
# Generalized cope helpers
# ---------------------------------------------------------

def target_axis_for_cope_specification(
    specification,
):
    """
    Return the target tube axis for a generalized cope.

    Unlike the legacy notch path, a cope target can be one
    member rather than a two-member straight-through pair.
    """

    target_member = (
        specification.target_member
    )

    return (
        node_vector(
            target_member.start
        ),
        node_vector(
            target_member.end
        ),
    )


def automatic_cope_specifications(
    frame,
):
    """
    Return generalized cope specifications using AUTO treatment.

    Automatic behavior intentionally remains unchanged:
    straight-through T-joints are resolved automatically,
    while corners receive no cope until a designer treatment
    is explicitly stored.
    """

    specifications = []

    for joint in detect_joints(
        frame
    ):
        treatment = (
            JointTreatment.automatic(
                joint
            )
        )

        specifications.extend(
            cope_specifications_for_treatment(
                treatment
            )
        )

    return tuple(
        specifications
    )


def configure_automatic_copes(
    frame,
    rendered_objects,
):
    """
    Apply generalized automatic cope information to rendered members.

    Domain members and rendered objects correspond by position
    in frame.members.
    """

    if (
        len(rendered_objects)
        != len(frame.members)
    ):
        raise ValueError(
            "Rendered member count does not match "
            "the domain frame."
        )

    object_by_member_identity = {
        id(member): obj
        for member, obj in zip(
            frame.members,
            rendered_objects,
        )
    }

    # Always clear existing metadata before applying the
    # treatment resolved from the current frame.
    for obj in rendered_objects:
        clear_notch(
            obj
        )

    configured_member_ids = set()

    for specification in (
        automatic_cope_specifications(
            frame
        )
    ):
        coped_key = id(
            specification.coped_member
        )

        coped_object = (
            object_by_member_identity.get(
                coped_key
            )
        )

        if coped_object is None:
            continue

        # Current FreeCAD member metadata stores one cope
        # operation per member. Multiple cope operations on
        # one member will be added in a later feature.
        if (
            coped_key
            in configured_member_ids
        ):
            raise ValueError(
                "Automatic cope generation currently "
                "supports one notched end per member."
            )

        target_start, target_end = (
            target_axis_for_cope_specification(
                specification
            )
        )

        configure_notch(
            coped_object,
            target_start,
            target_end,
            specification.target_outside_diameter,
        )

        configured_member_ids.add(
            coped_key
        )

    return rendered_objects


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

        obj.ViewObject.Visibility = (
            True
        )

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
        """Render every member and apply automatic tube copes."""

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

        # -------------------------------------------------
        # Render all members first
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Resolve AUTO joint treatments and configure their
        # generalized member-to-member cope operations.
        # -------------------------------------------------

        configure_automatic_copes(
            frame,
            rendered_objects,
        )

        # TubeMemberProxy.execute() regenerates configured
        # members through the persistent cope geometry path.
        document.recompute()

        return rendered_objects
    