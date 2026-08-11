"""FreeCAD adapter for resolving persisted ForgeCAD joint treatments."""

from forgecad.fabrication import (
    Joint,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
    JointTreatmentMode,
)
from forgecad.services.joint_treatment_resolver import (
    resolve_joint_treatment,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    frame_member_objects,
    member_from_freecad_object,
    member_touches_node,
)
from forgecad.adapters.freecad.joint_treatment_store import (
    load_joint_treatment,
    node_key,
)


def domain_member_records(
    document,
):
    """
    Return generated FreeCAD members paired with domain members.

    Keeping these paired preserves SourceLayoutID identity while
    allowing fabrication services to operate on domain members.
    """

    records = []

    for member_object in frame_member_objects(
        document
    ):
        records.append(
            (
                member_object,
                member_from_freecad_object(
                    member_object
                ),
            )
        )

    return tuple(
        records
    )


def connected_member_records(
    records,
    joint,
):
    """Return member records connected to a domain joint."""

    return tuple(
        (
            member_object,
            member,
        )
        for member_object, member in records
        if member_touches_node(
            member,
            joint.node,
        )
    )


def through_members_from_layout_ids(
    records,
    layout_ids,
):
    """Resolve persistent SourceLayoutID values to domain members."""

    requested_ids = tuple(
        str(
            layout_id
        ).strip()
        for layout_id in layout_ids
        if str(
            layout_id
        ).strip()
    )

    through_members = []

    for requested_id in requested_ids:
        for member_object, member in records:
            source_layout_id = str(
                getattr(
                    member_object,
                    "SourceLayoutID",
                    "",
                )
            ).strip()

            if (
                source_layout_id
                == requested_id
            ):
                through_members.append(
                    member
                )
                break

    return tuple(
        through_members
    )


def treatment_for_joint(
    document,
    joint,
    records,
):
    """
    Rebuild the persisted JointTreatment for a domain joint.

    The reconstructed joint and its selected through members use
    the same Member instances. This is required because fabrication
    treatment resolution uses member identity.

    None is returned when the joint has no saved treatment.
    """

    saved = load_joint_treatment(
        document,
        node_key(
            joint.node
        ),
    )

    if saved is None:
        return None

    mode_value, through_layout_ids = (
        saved
    )

    try:
        mode = JointTreatmentMode(
            mode_value
        )

    except ValueError:
        return None

    connected = connected_member_records(
        records,
        joint,
    )

    resolved_joint = Joint(
        node=joint.node,
        members=[
            member
            for member_object, member
            in connected
        ],
    )

    through_members = (
        through_members_from_layout_ids(
            connected,
            through_layout_ids,
        )
    )

    return JointTreatment(
        joint=resolved_joint,
        mode=mode,
        through_members=through_members,
    )


def joint_treatment_resolutions_for_document(
    document,
    joints,
):
    """Resolve all persisted treatments for document joints."""

    if document is None:
        return ()

    records = domain_member_records(
        document
    )

    resolutions = []

    for joint in joints:
        treatment = treatment_for_joint(
            document,
            joint,
            records,
        )

        if treatment is None:
            continue

        try:
            resolution = (
                resolve_joint_treatment(
                    treatment
                )
            )

        except ValueError:
            continue

        resolutions.append(
            resolution
        )

    return tuple(
        resolutions
    )
