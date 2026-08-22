"""FreeCAD integration helpers for splitting straight ForgeCAD members."""

from forgecad.adapters.freecad.commands.create_member_between_nodes import (
    create_member_between_nodes,
)
from forgecad.adapters.freecad.fabrication_refresh import (
    refresh_fabrication_for_document,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    structural_member_from_freecad_object,
)
from forgecad.adapters.freecad.member_removal import (
    remove_member_and_unused_layout,
)
from forgecad.adapters.freecad.topology_refresh import (
    refresh_joint_topology,
)
from forgecad.services.member_split import (
    split_member,
)


def split_member_object(
    document,
    member_object,
    split_point,
):
    """
    Replace one straight ForgeCAD member with two split members.

    The original member's profile and material are preserved. The split
    location becomes a persistent ForgeCAD node, reusing an existing node
    when one already exists at that point.
    """

    if document is None:
        raise ValueError(
            "Split Member requires an active document."
        )

    if member_object is None:
        raise ValueError(
            "Split Member requires a ForgeCAD member."
        )

    source_member = (
        structural_member_from_freecad_object(
            member_object
        )
    )

    first_member, second_member = (
        split_member(
            source_member,
            split_point,
        )
    )

    # Lazy import keeps this adapter testable outside the FreeCAD GUI runtime.
    from forgecad.adapters.freecad.commands.draw_member_interactive import (
        get_or_create_node,
    )

    start_node = get_or_create_node(
        document,
        first_member.start,
    )

    split_node = get_or_create_node(
        document,
        first_member.end,
    )

    end_node = get_or_create_node(
        document,
        second_member.end,
    )

    first_layout, first_object = (
        create_member_between_nodes(
            document,
            start_node,
            split_node,
            profile=source_member.profile,
            material=source_member.material,
            refresh=False,
        )
    )

    second_layout, second_object = (
        create_member_between_nodes(
            document,
            split_node,
            end_node,
            profile=source_member.profile,
            material=source_member.material,
            refresh=False,
        )
    )

    remove_member_and_unused_layout(
        document,
        member_object,
    )

    refresh_joint_topology(
        document
    )

    refresh_fabrication_for_document(
        document
    )

    document.recompute()

    return (
        first_layout,
        first_object,
        second_layout,
        second_object,
        split_node,
    )
