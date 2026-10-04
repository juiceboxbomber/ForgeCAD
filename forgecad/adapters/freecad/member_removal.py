"""Safe removal helpers for generated ForgeCAD straight members."""


def source_layout_id(
    member_object,
) -> str:
    """Return the persistent source layout ID for a member."""

    return str(
        getattr(
            member_object,
            "SourceLayoutID",
            "",
        )
    ).strip()


def member_objects(
    document,
):
    """Return generated straight-member objects from the Frame group."""

    if document is None:
        return ()

    frame_group = document.getObject(
        "ForgeCADFrame"
    )

    if frame_group is None:
        return ()

    return tuple(
        obj
        for obj in getattr(
            frame_group,
            "Group",
            ()
        )
        if hasattr(
            obj,
            "MemberID",
        )
        and hasattr(
            obj,
            "SourceLayoutID",
        )
    )


def layout_objects(
    document,
):
    """Return persistent ForgeCAD layout objects."""

    if document is None:
        return ()

    layout_group = document.getObject(
        "ForgeCADLayout"
    )

    if layout_group is None:
        return ()

    return tuple(
        getattr(
            layout_group,
            "Group",
            (),
        )
    )


def layout_object_for_id(
    document,
    requested_layout_id,
):
    """Return the layout object with a matching LayoutID."""

    requested_layout_id = str(
        requested_layout_id
    ).strip()

    if not requested_layout_id:
        return None

    for obj in layout_objects(
        document
    ):
        if (
            str(
                getattr(
                    obj,
                    "LayoutID",
                    "",
                )
            ).strip()
            == requested_layout_id
        ):
            return obj

    return None


def other_members_using_layout(
    document,
    requested_layout_id,
    excluded_member=None,
):
    """Return other frame members referencing one layout ID."""

    requested_layout_id = str(
        requested_layout_id
    ).strip()

    return tuple(
        obj
        for obj in member_objects(
            document
        )
        if obj is not excluded_member
        and source_layout_id(
            obj
        )
        == requested_layout_id
    )


def bent_source_layout_ids(member_object):
    identifiers = []

    for reference in getattr(member_object, "SourceLayoutLines", ()):
        if isinstance(reference, str):
            layout_id = reference.strip()
        else:
            layout_id = str(getattr(reference, "LayoutID", "")).strip()

        if layout_id and layout_id not in identifiers:
            identifiers.append(layout_id)

    for property_name in (
        "StartFabricationLayoutID",
        "EndFabricationLayoutID",
    ):
        layout_id = str(getattr(member_object, property_name, "")).strip()
        if layout_id and layout_id not in identifiers:
            identifiers.append(layout_id)

    return tuple(identifiers)


def object_uses_layout_id(obj, requested_layout_id):
    requested_layout_id = str(requested_layout_id).strip()
    if not requested_layout_id:
        return False

    if source_layout_id(obj) == requested_layout_id:
        return True

    return requested_layout_id in bent_source_layout_ids(obj)


def other_structural_objects_using_layout(
    document,
    requested_layout_id,
    excluded_member=None,
):
    if document is None:
        return ()

    frame_group = document.getObject("ForgeCADFrame")
    if frame_group is None:
        return ()

    return tuple(
        obj
        for obj in getattr(frame_group, "Group", ())
        if obj is not excluded_member
        and object_uses_layout_id(obj, requested_layout_id)
    )


def remove_bent_member_and_unused_layouts(
    document,
    member_object,
):
    if document is None or member_object is None:
        return False

    member_name = str(getattr(member_object, "Name", "")).strip()
    if not member_name:
        raise ValueError("ForgeCAD bent member has no document object name.")

    layout_ids = bent_source_layout_ids(member_object)
    removable_layouts = []

    for layout_id in layout_ids:
        layout_object = layout_object_for_id(document, layout_id)
        if layout_object is None:
            continue

        keep_layout = bool(
            other_structural_objects_using_layout(
                document,
                layout_id,
                excluded_member=member_object,
            )
        )
        if not keep_layout:
            removable_layouts.append(layout_object)

    frame_group = document.getObject("ForgeCADFrame")
    layout_group = document.getObject("ForgeCADLayout")

    remove_object_from_group(frame_group, member_object)
    document.removeObject(member_name)

    for layout_object in removable_layouts:
        remove_object_from_group(layout_group, layout_object)
        document.removeObject(layout_object.Name)

    document.recompute()
    return True

def remove_object_from_group(
    group,
    obj,
):
    """Remove an object from a group when possible."""

    if (
        group is None
        or obj is None
    ):
        return

    try:
        group.removeObject(
            obj
        )
    except Exception:
        pass


def remove_member_and_unused_layout(
    document,
    member_object,
):
    """
    Remove one generated straight member and its unused source layout.

    Endpoint nodes are deliberately preserved.

    The source layout object is removed only when no other generated
    member references the same LayoutID.
    """

    if (
        document is None
        or member_object is None
    ):
        return False

    member_name = str(
        getattr(
            member_object,
            "Name",
            "",
        )
    ).strip()

    if not member_name:
        raise ValueError(
            "ForgeCAD member has no document object name."
        )

    layout_id = source_layout_id(
        member_object
    )

    frame_group = document.getObject(
        "ForgeCADFrame"
    )

    layout_group = document.getObject(
        "ForgeCADLayout"
    )

    layout_object = (
        layout_object_for_id(
            document,
            layout_id,
        )
        if layout_id
        else None
    )

    keep_layout = bool(
        other_members_using_layout(
            document,
            layout_id,
            excluded_member=member_object,
        )
    )

    remove_object_from_group(
        frame_group,
        member_object,
    )

    document.removeObject(
        member_name
    )

    if (
        layout_object is not None
        and not keep_layout
    ):
        remove_object_from_group(
            layout_group,
            layout_object,
        )

        document.removeObject(
            layout_object.Name
        )

    document.recompute()

    return True
