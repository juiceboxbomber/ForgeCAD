"""Reapply ForgeCAD fabrication geometry to existing document members."""


def refresh_fabrication_for_document(
    document,
):
    """
    Recalculate fabrication treatments on existing structural objects.

    Converted bent tubes participate through separate persistent start/end
    fabrication identities rather than pretending the whole bend owns one
    SourceLayoutID.
    """

    if document is None:
        return False

    from forgecad.fabrication import (
        Frame,
    )
    from forgecad.adapters.freecad.joint_inspector_adapter import (
        frame_member_objects,
        structural_member_from_freecad_object,
    )
    from forgecad.adapters.freecad.renderer import (
        configure_saved_fabrication,
    )
    from forgecad.services.fabrication_identity import (
        fabrication_endpoint_ids,
    )

    structural_objects = list(
        frame_member_objects(
            document
        )
    )

    if not structural_objects:
        return False

    frame = Frame(
        members=[
            structural_member_from_freecad_object(
                obj
            )
            for obj
            in structural_objects
        ]
    )

    source_layout_ids = []

    for obj in structural_objects:
        straight_id = str(
            getattr(
                obj,
                "SourceLayoutID",
                "",
            )
            or ""
        ).strip()

        if straight_id:
            source_layout_ids.append(
                straight_id
            )
            continue

        try:
            source_layout_ids.append(
                fabrication_endpoint_ids(
                    obj
                )
            )
        except ValueError:
            source_layout_ids.append(
                ""
            )

    configure_saved_fabrication(
        document,
        frame,
        structural_objects,
        source_layout_ids=(
            source_layout_ids
        ),
    )

    for obj in structural_objects:
        proxy = getattr(
            obj,
            "Proxy",
            None,
        )

        if (
            proxy is not None
            and hasattr(
                proxy,
                "update_shape",
            )
        ):
            proxy.update_shape(
                obj
            )

        try:
            obj.touch()
        except Exception:
            pass

    document.recompute()

    return True
