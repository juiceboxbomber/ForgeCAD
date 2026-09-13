"""Pure selection helpers for ForgeCAD's direct Miter Selected command."""


def _layout_id(obj):
    return str(getattr(obj, "SourceLayoutID", "") or "").strip()


def _xyz(point):
    return (float(point.x), float(point.y), float(point.z))


def _point_key(point, precision=6):
    return tuple(round(value, precision) for value in _xyz(point))


def _end_keys(obj, precision=6):
    if not hasattr(obj, "StartPoint") or not hasattr(obj, "EndPoint"):
        raise ValueError("Select only straight generated ForgeCAD members.")
    return {
        _point_key(obj.StartPoint, precision),
        _point_key(obj.EndPoint, precision),
    }


def selected_miter_request(
    objects,
    precision=6,
):
    """Resolve two straight-or-bent structural tubes at one shared endpoint."""

    objects = list(
        objects
        or ()
    )

    if len(
        objects
    ) != 2:
        raise ValueError(
            "Select exactly two tubes to miter together."
        )

    from forgecad.services.fabrication_identity import (
        shared_structural_endpoint,
    )

    node_xyz, member_ids = (
        shared_structural_endpoint(
            objects,
            precision=precision,
        )
    )

    return (
        node_xyz,
        member_ids,
    )
