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
from forgecad.services.joint_extension import (
    MEMBER_END_END,
    MEMBER_END_START,
    extension_specifications_for_treatment,
)
from forgecad.services.joint_miter import (
    MITER_END_END,
    MITER_END_START,
    miter_specifications_for_treatment,
)
from forgecad.services.notch_analysis import (
    BRANCH_END_END,
    BRANCH_END_START,
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
    clear_extensions,
    clear_miter,
    clear_notch,
    configure_end_cope,
    configure_end_cope_secondary,
    configure_end_extension,
    configure_end_miter,
    configure_start_cope,
    configure_start_cope_secondary,
    configure_start_extension,
    configure_start_miter,
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
# ---------------------------------------------------------

def through_axis_for_specification(
    specification,
):
    """Return a continuous FreeCAD axis for a legacy notch cutter."""

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
    Apply legacy automatic-notch information by member end.

    A member may be coped once at its start and once at its end.
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

    configured_member_ends = set()

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

        branch_end = (
            specification.branch_end
        )

        configuration_key = (
            branch_key,
            branch_end,
        )

        if (
            configuration_key
            in configured_member_ends
        ):
            raise ValueError(
                "Automatic notch generation received "
                "more than one cope for the same member end."
            )

        through_start, through_end = (
            through_axis_for_specification(
                specification
            )
        )

        if (
            branch_end
            == BRANCH_END_START
        ):
            configure_start_cope(
                branch_object,
                through_start,
                through_end,
                specification.through_outside_diameter,
            )

        elif (
            branch_end
            == BRANCH_END_END
        ):
            configure_end_cope(
                branch_object,
                through_start,
                through_end,
                specification.through_outside_diameter,
            )

        else:
            raise ValueError(
                "Unknown automatic-notch member end."
            )

        configured_member_ends.add(
            configuration_key
        )

    return rendered_objects


# ---------------------------------------------------------
# Generalized treatment helpers
# ---------------------------------------------------------

def target_axis_for_cope_specification(
    specification,
):
    """Return the target member centerline for a cope cutter."""

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
    """Map domain-member identity to persistent layout ID."""

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
    """Return the joint member associated with a persistent layout ID."""

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

    Invalid or stale references safely fall back to AUTO.
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


def treatments_for_frame(
    document,
    frame,
    source_layout_ids=None,
):
    """Return saved-or-automatic treatment for every joint."""

    layout_ids_by_member = (
        member_layout_id_map(
            frame,
            source_layout_ids,
        )
    )

    treatments = []

    for joint in detect_joints(
        frame
    ):
        treatments.append(
            saved_treatment_for_joint(
                document,
                joint,
                layout_ids_by_member,
            )
        )

    return tuple(
        treatments
    )


def cope_specifications_for_frame(
    document,
    frame,
    source_layout_ids=None,
):
    """Return all cylindrical cope specifications for a frame."""

    specifications = []

    for treatment in treatments_for_frame(
        document,
        frame,
        source_layout_ids=source_layout_ids,
    ):
        specifications.extend(
            cope_specifications_for_treatment(
                treatment
            )
        )

    return tuple(
        specifications
    )


def extension_specifications_for_frame(
    document,
    frame,
    source_layout_ids=None,
):
    """Return all physical member extensions required by treatments."""

    specifications = []

    for treatment in treatments_for_frame(
        document,
        frame,
        source_layout_ids=source_layout_ids,
    ):
        specifications.extend(
            extension_specifications_for_treatment(
                treatment
            )
        )

    return tuple(
        specifications
    )


def miter_specifications_for_frame(
    document,
    frame,
    source_layout_ids=None,
):
    """Return all planar miter specifications for a frame."""

    specifications = []

    for treatment in treatments_for_frame(
        document,
        frame,
        source_layout_ids=source_layout_ids,
    ):
        specifications.extend(
            miter_specifications_for_treatment(
                treatment
            )
        )

    return tuple(
        specifications
    )


def automatic_cope_specifications(
    frame,
):
    """Return generalized cope specifications using AUTO treatment."""

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
    clear_existing=True,
):
    """
    Apply cylindrical cope specifications by member end.

    A member may have up to two sequential cylindrical copes at
    its start and up to two at its end. The first specification
    uses the primary cope slot and the second uses the secondary
    cope slot.
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

    if clear_existing:
        for obj in rendered_objects:
            clear_notch(
                obj
            )

    configured_member_end_counts = {}

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

        coped_end = (
            specification.coped_end
        )

        configuration_key = (
            coped_key,
            coped_end,
        )

        cope_index = (
            configured_member_end_counts.get(
                configuration_key,
                0,
            )
        )

        if cope_index >= 2:
            raise ValueError(
                "Cope generation received more than "
                "two treatments for the same member end."
            )

        target_start, target_end = (
            target_axis_for_cope_specification(
                specification
            )
        )

        if (
            coped_end
            == BRANCH_END_START
        ):
            if cope_index == 0:
                configure_start_cope(
                    coped_object,
                    target_start,
                    target_end,
                    specification.target_outside_diameter,
                )

            else:
                configure_start_cope_secondary(
                    coped_object,
                    target_start,
                    target_end,
                    specification.target_outside_diameter,
                )

        elif (
            coped_end
            == BRANCH_END_END
        ):
            if cope_index == 0:
                configure_end_cope(
                    coped_object,
                    target_start,
                    target_end,
                    specification.target_outside_diameter,
                )

            else:
                configure_end_cope_secondary(
                    coped_object,
                    target_start,
                    target_end,
                    specification.target_outside_diameter,
                )

        else:
            raise ValueError(
                "Unknown cope member end."
            )

        configured_member_end_counts[
            configuration_key
        ] = (
            cope_index + 1
        )

    return rendered_objects


def configure_extension_specifications(
    frame,
    rendered_objects,
    specifications,
    clear_existing=True,
):
    """
    Apply physical member-end extensions.

    Multiple joints may affect opposite ends of the same member.
    If several requirements affect the same end, the largest wins.
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

    if clear_existing:
        for obj in rendered_objects:
            clear_extensions(
                obj
            )

    start_extensions = {}
    end_extensions = {}

    for specification in specifications:
        member_key = id(
            specification.member
        )

        if (
            member_key
            not in object_by_member_identity
        ):
            continue

        extension = float(
            specification.extension_mm
        )

        if (
            specification.member_end
            == MEMBER_END_START
        ):
            start_extensions[
                member_key
            ] = max(
                start_extensions.get(
                    member_key,
                    0.0,
                ),
                extension,
            )

        elif (
            specification.member_end
            == MEMBER_END_END
        ):
            end_extensions[
                member_key
            ] = max(
                end_extensions.get(
                    member_key,
                    0.0,
                ),
                extension,
            )

        else:
            raise ValueError(
                "Unknown member extension end."
            )

    for (
        member_key,
        extension,
    ) in start_extensions.items():
        configure_start_extension(
            object_by_member_identity[
                member_key
            ],
            extension,
        )

    for (
        member_key,
        extension,
    ) in end_extensions.items():
        configure_end_extension(
            object_by_member_identity[
                member_key
            ],
            extension,
        )

    return rendered_objects


def configure_miter_specifications(
    frame,
    rendered_objects,
    specifications,
    clear_existing=True,
):
    """
    Apply planar miter specifications to rendered members.

    A member may have one miter at its start and one miter at
    its end. Two independent end treatments on the same physical
    tube are therefore valid.

    Conflicting specifications for the same member end are
    rejected.
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

    if clear_existing:
        for obj in rendered_objects:
            clear_miter(
                obj
            )

    configured_member_ends = set()

    for specification in specifications:
        member_key = id(
            specification.member
        )

        member_object = (
            object_by_member_identity.get(
                member_key
            )
        )

        if member_object is None:
            continue

        member_end = (
            specification.member_end
        )

        configuration_key = (
            member_key,
            member_end,
        )

        if (
            configuration_key
            in configured_member_ends
        ):
            raise ValueError(
                "Miter generation received more than "
                "one treatment for the same member end."
            )

        plane_point = FreeCAD.Vector(
            specification.plane_point[
                0
            ],
            specification.plane_point[
                1
            ],
            specification.plane_point[
                2
            ],
        )

        plane_normal = FreeCAD.Vector(
            specification.plane_normal[
                0
            ],
            specification.plane_normal[
                1
            ],
            specification.plane_normal[
                2
            ],
        )

        keep_point = FreeCAD.Vector(
            specification.keep_point[
                0
            ],
            specification.keep_point[
                1
            ],
            specification.keep_point[
                2
            ],
        )

        if (
            member_end
            == MITER_END_START
        ):
            configure_start_miter(
                member_object,
                plane_point,
                plane_normal,
                keep_point,
            )

        elif (
            member_end
            == MITER_END_END
        ):
            configure_end_miter(
                member_object,
                plane_point,
                plane_normal,
                keep_point,
            )

        else:
            raise ValueError(
                "Unknown miter member end."
            )

        configured_member_ends.add(
            configuration_key
        )

    return rendered_objects


def configure_automatic_copes(
    frame,
    rendered_objects,
):
    """Apply generalized AUTO cope information."""

    return configure_cope_specifications(
        frame,
        rendered_objects,
        automatic_cope_specifications(
            frame
        ),
    )


def configure_saved_fabrication(
    document,
    frame,
    rendered_objects,
    source_layout_ids=None,
):
    """
    Apply saved fabrication treatment.

    Processing order:

        physical extension
        start/end cylindrical copes
        start/end planar miters
    """

    extension_specs = (
        extension_specifications_for_frame(
            document,
            frame,
            source_layout_ids=(
                source_layout_ids
            ),
        )
    )

    cope_specs = (
        cope_specifications_for_frame(
            document,
            frame,
            source_layout_ids=(
                source_layout_ids
            ),
        )
    )

    miter_specs = (
        miter_specifications_for_frame(
            document,
            frame,
            source_layout_ids=(
                source_layout_ids
            ),
        )
    )

    for obj in rendered_objects:
        clear_extensions(
            obj
        )

        clear_notch(
            obj
        )

        clear_miter(
            obj
        )

    configure_extension_specifications(
        frame,
        rendered_objects,
        extension_specs,
        clear_existing=False,
    )

    configure_cope_specifications(
        frame,
        rendered_objects,
        cope_specs,
        clear_existing=False,
    )

    configure_miter_specifications(
        frame,
        rendered_objects,
        miter_specs,
        clear_existing=False,
    )

    return rendered_objects


def configure_saved_copes(
    document,
    frame,
    rendered_objects,
    source_layout_ids=None,
):
    """Compatibility wrapper for saved fabrication."""

    return configure_saved_fabrication(
        document,
        frame,
        rendered_objects,
        source_layout_ids=(
            source_layout_ids
        ),
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

        obj.Label = (
            "Tube Member"
        )

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
        """Render every member and apply saved fabrication treatment."""

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

        configure_saved_fabrication(
            document,
            frame,
            rendered_objects,
            source_layout_ids=(
                source_layout_ids
            ),
        )

        document.recompute()

        return rendered_objects
