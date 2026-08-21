"""Reapply ForgeCAD fabrication geometry to existing document members."""


def refresh_fabrication_for_document(
    document,
):
    """
    Recalculate fabrication treatments on existing structural objects.

    Existing member objects are retained. Cope, miter, and extension
    metadata is recalculated from the current structural geometry.
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
            for obj in structural_objects
        ]
    )

    source_layout_ids = [
        str(
            getattr(
                obj,
                "SourceLayoutID",
                "",
            )
        ).strip()
        for obj in structural_objects
    ]

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
