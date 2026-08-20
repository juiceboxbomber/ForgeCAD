"""FreeCAD adapter helpers for ForgeCAD joint inspection."""

from forgecad.fabrication import (
    BentMember,
    Joint,
    Member,
    Node,
)
from forgecad.geometry import (
    Point3D,
    Vector3D,
)
from forgecad.services import (
    create_default_material,
    create_default_tube_library,
)
from forgecad.services.bent_tube_path import (
    build_bent_tube_centerline,
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
    """Return True when an object contains straight-member data."""

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


def is_forgecad_bent_member(
    obj,
):
    """Return True when an object contains ForgeCAD bent-tube data."""

    if obj is None:
        return False

    required_properties = (
        "StartPoint",
        "InitialDirection",
        "InitialBendNormal",
        "TubeProfile",
        "BendCount",
    )

    if not all(
        hasattr(
            obj,
            property_name,
        )
        for property_name
        in required_properties
    ):
        return False

    proxy = getattr(
        obj,
        "Proxy",
        None,
    )

    return (
        proxy is not None
        and hasattr(
            proxy,
            "_tube_from_properties",
        )
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
    """Return the domain tube profile used by a straight FreeCAD member."""

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
    Return the material represented by a straight FreeCAD member.

    ForgeCAD currently has one domain default material, so use
    that material when rebuilding members for joint analysis.
    """

    return create_default_material()


def member_from_freecad_object(
    obj,
):
    """Build a domain Member from a generated FreeCAD straight member."""

    if not is_forgecad_member(
        obj
    ):
        raise ValueError(
            "Object is not a ForgeCAD straight member."
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


def bent_member_from_freecad_object(
    obj,
):
    """
    Build a domain BentMember from a parametric FreeCAD bent tube.

    The end node is taken from the solved bent-tube centerline rather
    than from a straight start-to-end chord.
    """

    if not is_forgecad_bent_member(
        obj
    ):
        raise ValueError(
            "Object is not a ForgeCAD bent member."
        )

    tube = obj.Proxy._tube_from_properties(
        obj
    )

    start_vector = obj.StartPoint
    direction_vector = obj.InitialDirection
    normal_vector = obj.InitialBendNormal

    start_point = Point3D(
        float(start_vector.x),
        float(start_vector.y),
        float(start_vector.z),
    )

    initial_direction = Vector3D(
        float(direction_vector.x),
        float(direction_vector.y),
        float(direction_vector.z),
    )

    initial_bend_normal = Vector3D(
        float(normal_vector.x),
        float(normal_vector.y),
        float(normal_vector.z),
    )

    centerline = build_bent_tube_centerline(
        tube,
        start_point=start_point,
        initial_direction=initial_direction,
        initial_bend_normal=initial_bend_normal,
    )

    return BentMember(
        start=Node(
            centerline.start_point.x,
            centerline.start_point.y,
            centerline.start_point.z,
        ),
        end=Node(
            centerline.end_point.x,
            centerline.end_point.y,
            centerline.end_point.z,
        ),
        tube=tube,
        initial_direction=initial_direction,
        initial_bend_normal=initial_bend_normal,
    )


def structural_member_from_freecad_object(
    obj,
):
    """Build either a straight Member or BentMember from a FreeCAD object."""

    if is_forgecad_member(
        obj
    ):
        return member_from_freecad_object(
            obj
        )

    if is_forgecad_bent_member(
        obj
    ):
        return bent_member_from_freecad_object(
            obj
        )

    raise ValueError(
        "Object is not a ForgeCAD structural member."
    )


def frame_member_objects(
    document,
):
    """
    Return all FreeCAD structural-member objects in the project.

    Straight members live in the Frame group. Bent structural members
    currently live in the Bent Tubes group.
    """

    if document is None:
        return []

    objects = []

    frame_group = document.getObject(
        "ForgeCADFrame"
    )

    if frame_group is not None:
        objects.extend(
            obj
            for obj in frame_group.Group
            if is_forgecad_member(
                obj
            )
        )

    bent_group = document.getObject(
        "ForgeCADBentTubes"
    )

    if bent_group is not None:
        objects.extend(
            obj
            for obj in bent_group.Group
            if is_forgecad_bent_member(
                obj
            )
        )

    return objects


def joint_from_node_object(
    document,
    node_object,
):
    """
    Rebuild the domain Joint represented by a FreeCAD node.

    Straight frame members may connect at endpoints or pass through the
    node interior. Bent members currently participate through their true
    solved start and end nodes.
    """

    node = node_from_freecad_object(
        node_object
    )

    connected = []

    for obj in frame_member_objects(
        document
    ):
        member = (
            structural_member_from_freecad_object(
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
