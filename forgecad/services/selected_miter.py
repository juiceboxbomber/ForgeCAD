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


def selected_miter_request(objects, precision=6):
    """Resolve two selected members and their one shared design endpoint.

    Selection is direct and intentionally ignores existing fabrication metadata.
    The selected pair may belong to a larger three-, four-, or higher-member joint.
    """
    objects = list(objects or ())
    if len(objects) != 2:
        raise ValueError("Select exactly two tubes to miter together.")

    ids = []
    common = None
    for obj in objects:
        ident = _layout_id(obj)
        if not ident:
            raise ValueError(
                "Every selected tube must be a generated ForgeCAD member with a SourceLayoutID."
            )
        if ident in ids:
            raise ValueError("Select two different tubes.")
        ids.append(ident)
        ends = _end_keys(obj, precision)
        common = ends if common is None else common.intersection(ends)

    if len(common or ()) != 1:
        raise ValueError("The selected tubes must share exactly one joint endpoint.")

    return next(iter(common)), tuple(ids)
