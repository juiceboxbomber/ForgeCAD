"""FreeCAD adapter helpers for ForgeCAD joint inspection."""

from forgecad.fabrication import (
    Joint,
    Member,
    Node,
)
from forgecad.services import (
    create_default_material,
    create_default_tube_library,
)
from forgecad.services.joint_service import (
    member_touches_node,
)


def is_forgecad_node(
    obj,
):
    """Return True when an object is a ForgeCAD node."""

    if obj is None:
        return False

    required_properties = (
        "NodeID",
        "Position",
    )

    return all(
        hasattr(
            obj,
            property_name,
        )
        for property_name
        in required_properties
    )


def is_forgecad_member(
    obj,
):
    """Return True when an object contains member geometry data."""

    if obj is None:
        return False

    required_properties = (
        "MemberID",
        "TubeProfile",
        "StartPoint",
        "EndPoint",
    )

    return all(
        hasattr(
            obj,
            property_name,
        )
        for property_name
        in required_properties
    )


def node_from_freecad_object(
    obj,
):
    """Build a domain Node from a FreeCAD node object."""

    if not is_forgecad_node(
        obj
    ):
        raise ValueError(
            "Object is not a ForgeCAD node."
        )

    position = obj.Position

    return Node(
        float(position.x),
        float(position.y),
        float(position.z),
    )


def profile_from_member_object(
    obj,
):
    """Return the domain tube profile used by a FreeCAD member."""

    library = (
        create_default_tube_library()
    )

    profile_name = str(
        obj.TubeProfile
    )

    try:
        return library.get(
            profile_name
        )

    except KeyError as error:
        raise ValueError(
            f"Unknown ForgeCAD tube profile: "
            f"{profile_name}"
        ) from error


def material_from_member_object(
    obj,
):
    """
    Return the material represented by a FreeCAD member.

    ForgeCAD currently has one domain default material, so use
    that material when rebuilding members for joint analysis.
    """

    return create_default_material()


def member_from_freecad_object(
    obj,
):
    """Build a domain Member from a generated FreeCAD member."""

    if not is_forgecad_member(
        obj
    ):
        raise ValueError(
            "Object is not a ForgeCAD member."
        )

    start = obj.StartPoint
    end = obj.EndPoint

    return Member(
        start=Node(
            float(start.x),
            float(start.y),
            float(start.z),
        ),
        end=Node(
            float(end.x),
            float(end.y),
            float(end.z),
        ),
        profile=profile_from_member_object(
            obj
        ),
        material=material_from_member_object(
            obj
        ),
    )


def frame_member_objects(
    document,
):
    """Return generated member objects from the Frame group."""

    if document is None:
        return []

    frame_group = document.getObject(
        "ForgeCADFrame"
    )

    if frame_group is None:
        return []

    return [
        obj
        for obj in frame_group.Group
        if is_forgecad_member(
            obj
        )
    ]


def joint_from_node_object(
    document,
    node_object,
):
    """
    Rebuild the domain Joint represented by a FreeCAD node.

    Generated frame members are included when the node lies
    anywhere on the member centerline segment, including the
    interior of a continuous through member.
    """

    node = node_from_freecad_object(
        node_object
    )

    connected = []

    for obj in frame_member_objects(
        document
    ):
        member = (
            member_from_freecad_object(
                obj
            )
        )

        if member_touches_node(
            member,
            node,
        ):
            connected.append(
                member
            )

    return Joint(
        node=node,
        members=connected,
    )
