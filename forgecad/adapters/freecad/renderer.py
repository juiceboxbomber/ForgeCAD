"""Rendering of ForgeCAD objects into FreeCAD."""

import Part
import FreeCAD

from forgecad.fabrication import (
    Frame,
    Member,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
    JointTreatmentMode,
)
from forgecad.services import (
    detect_joints,
    member_other_node,
    notch_specifications_for_joint,
)
from forgecad.services.notch_analysis import (
    cope_specifications_for_treatment,
)
from forgecad.adapters.freecad.joint_treatment_store import (
    load_joint_treatment,
    node_key,
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

    A generalized cope targets one actual member rather than
    requiring a two-member straight-through pair.
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


def member_layout_id_map(
    frame,
    source_layout_ids,
):
    """Map domain-member identity to its persistent layout ID."""

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

    return {
        id(member): str(
            source_layout_id
        ).strip()
        for member, source_layout_id
        in zip(
            frame.members,
            source_layout_ids,
        )
    }


def member_for_layout_id(
    joint,
    layout_id,
    layout_ids_by_member,
):
    """
    Return the joint member associated with a layout ID.

    Only members belonging to the requested joint are searched.
    """

    requested_id = str(
        layout_id
    ).strip()

    if not requested_id:
        return None

    for member in joint.members:
        member_layout_id = (
            layout_ids_by_member.get(
                id(member),
                "",
            )
        )

        if (
            str(
                member_layout_id
            ).strip()
            == requested_id
        ):
            return member

    return None


def saved_treatment_for_joint(
    document,
    joint,
    layout_ids_by_member,
):
    """
    Rebuild a JointTreatment from persistent FreeCAD data.

    Invalid or stale persistent references safely fall back
    to automatic treatment.
    """

    automatic = (
        JointTreatment.automatic(
            joint
        )
    )

    if document is None:
        return automatic

    stored = load_joint_treatment(
        document,
        node_key(
            joint.node
        ),
    )

    if stored is None:
        return automatic

    mode_value, through_layout_ids = (
        stored
    )

    try:
        mode = JointTreatmentMode(
            mode_value
        )
    except ValueError:
        return automatic

    if (
        mode
        == JointTreatmentMode.AUTO
    ):
        return automatic

    if (
        mode
        == JointTreatmentMode.BOTH_COPED
    ):
        if (
            joint.member_count
            != 2
        ):
            return automatic

        return JointTreatment.both_coped(
            joint
        )

    if (
        mode
        == JointTreatmentMode.MEMBER_THROUGH
    ):
        if (
            len(
                through_layout_ids
            )
            != 1
        ):
            return automatic

        through_member = (
            member_for_layout_id(
                joint,
                through_layout_ids[
                    0
                ],
                layout_ids_by_member,
            )
        )

        if through_member is None:
            return automatic

        return JointTreatment.member_through(
            joint,
            through_member,
        )

    if (
        mode
        == JointTreatmentMode.THROUGH_PAIR
    ):
        if (
            len(
                through_layout_ids
            )
            != 2
        ):
            return automatic

        first_member = (
            member_for_layout_id(
                joint,
                through_layout_ids[
                    0
                ],
                layout_ids_by_member,
            )
        )

        second_member = (
            member_for_layout_id(
                joint,
                through_layout_ids[
                    1
                ],
                layout_ids_by_member,
            )
        )

        if (
            first_member is None
            or second_member is None
            or first_member
            is second_member
        ):
            return automatic

        return JointTreatment.through_pair(
            joint,
            first_member,
            second_member,
        )

    return automatic


def cope_specifications_for_frame(
    document,
    frame,
    source_layout_ids=None,
):
    """
    Return generalized cope specifications for a frame.

    Saved joint treatments override automatic behavior.
    Joints without a valid saved treatment use AUTO.
    """

    layout_ids_by_member = (
        member_layout_id_map(
            frame,
            source_layout_ids,
        )
    )

    specifications = []

    for joint in detect_joints(
        frame
    ):
        treatment = (
            saved_treatment_for_joint(
                document,
                joint,
                layout_ids_by_member,
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


def automatic_cope_specifications(
    frame,
):
    """
    Return generalized cope specifications using AUTO treatment.

    This helper remains available for compatibility and tests.
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


def configure_cope_specifications(
    frame,
    rendered_objects,
    specifications,
):
    """Apply generalized cope specifications to rendered members."""

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

    for specification in specifications:
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

        # Current member metadata supports one cope operation
        # per member. This is sufficient for either-through and
        # both-coped two-member corners.
        if (
            coped_key
            in configured_member_ids
        ):
            raise ValueError(
                "Cope generation currently supports "
                "one notched end per member."
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


def configure_automatic_copes(
    frame,
    rendered_objects,
):
    """
    Apply generalized AUTO cope information to rendered members.

    This helper remains available for compatibility.
    """

    return configure_cope_specifications(
        frame,
        rendered_objects,
        automatic_cope_specifications(
            frame
        ),
    )


def configure_saved_copes(
    document,
    frame,
    rendered_objects,
    source_layout_ids=None,
):
    """
    Apply saved treatments, falling back to AUTO where needed.
    """

    specifications = (
        cope_specifications_for_frame(
            document,
            frame,
            source_layout_ids=(
                source_layout_ids
            ),
        )
    )

    return configure_cope_specifications(
        frame,
        rendered_objects,
        specifications,
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
        """
        Render every member and apply persisted joint treatments.

        Joints without a stored treatment continue to use
        ForgeCAD's automatic treatment.
        """

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
        # Load persistent joint treatments.
        #
        # Missing or stale treatments automatically fall back
        # to ForgeCAD's existing geometric behavior.
        # -------------------------------------------------

        configure_saved_copes(
            document,
            frame,
            rendered_objects,
            source_layout_ids=(
                source_layout_ids
            ),
        )

        # TubeMemberProxy.execute() regenerates configured
        # members through the persistent cope geometry path.
        document.recompute()

        return rendered_objects
    