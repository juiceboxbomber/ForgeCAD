"""Pure helpers for ForgeCAD's direct selection-driven cope command."""


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


def selected_cope_request(objects, precision=6):
    """Resolve source, targets, and their one shared design endpoint.

    Selection order is intentional: first object is the tube being coped;
    the second and optional third objects are targets. Fabrication metadata
    such as miter state is deliberately ignored here: an already-mitered
    member is a valid cope *target*.
    """
    objects = list(objects or ())
    if len(objects) not in (2, 3):
        raise ValueError(
            "Select the tube to cope first, then one or two target tubes."
        )

    ids = []
    common = None
    for obj in objects:
        ident = _layout_id(obj)
        if not ident:
            raise ValueError(
                "Every selected tube must be a generated ForgeCAD member with a SourceLayoutID."
            )
        if ident in ids:
            raise ValueError("Select each tube only once.")
        ids.append(ident)
        ends = _end_keys(obj, precision)
        common = ends if common is None else common.intersection(ends)

    if len(common or ()) != 1:
        raise ValueError(
            "The selected tubes must share exactly one joint endpoint."
        )

    node_xyz = next(iter(common))
    return node_xyz, ids[0], tuple(ids[1:])


def replace_source_pairs(existing_pairs, source_id, target_ids):
    """Replace only one source member's additive cope targets."""
    source_id = str(source_id or "").strip()
    targets = tuple(str(value or "").strip() for value in target_ids)
    if not source_id or len(targets) not in (1, 2):
        raise ValueError("A cope requires one source and one or two targets.")
    if any(not target or target == source_id for target in targets):
        raise ValueError("Cope targets must be different from the coped tube.")
    if len(set(targets)) != len(targets):
        raise ValueError("Cope targets must be different from each other.")

    kept = []
    for pair in existing_pairs or ():
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("A stored cope pair is malformed.")
        old_source = str(pair[0] or "").strip()
        old_target = str(pair[1] or "").strip()
        if not old_source or not old_target or old_source == old_target:
            raise ValueError("A stored cope pair is malformed.")
        if old_source != source_id:
            value = (old_source, old_target)
            if value not in kept:
                kept.append(value)

    kept.extend((source_id, target) for target in targets)
    return tuple(kept)
