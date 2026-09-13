"""Pure helpers for ForgeCAD's direct Through Selected command."""

from math import sqrt


DEFAULT_POINT_TOLERANCE = 1e-5


def _layout_id(obj):
    return str(getattr(obj, "SourceLayoutID", "") or "").strip()


def _xyz(point):
    return (float(point.x), float(point.y), float(point.z))


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, scalar):
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _length(a):
    return sqrt(_dot(a, a))


def _distance(a, b):
    return _length(_sub(a, b))


def _point_key_xyz(value, precision=6):
    return tuple(round(float(component), precision) for component in value)


def _end_xyz(obj):
    if not hasattr(obj, "StartPoint") or not hasattr(obj, "EndPoint"):
        raise ValueError("Select only straight generated ForgeCAD members.")
    return (_xyz(obj.StartPoint), _xyz(obj.EndPoint))


def point_on_segment(point, start, end, tolerance=DEFAULT_POINT_TOLERANCE):
    """Return True when an XYZ point lies on a finite segment."""
    point = tuple(map(float, point))
    start = tuple(map(float, start))
    end = tuple(map(float, end))
    segment = _sub(end, start)
    length_squared = _dot(segment, segment)
    if length_squared <= 1e-24:
        return _distance(point, start) <= tolerance
    parameter = _dot(_sub(point, start), segment) / length_squared
    if parameter < -tolerance or parameter > 1.0 + tolerance:
        return False
    parameter = max(0.0, min(1.0, parameter))
    closest = _add(start, _mul(segment, parameter))
    return _distance(point, closest) <= tolerance


def point_strictly_inside_segment(point, start, end, tolerance=DEFAULT_POINT_TOLERANCE):
    """Return True for a point on a segment but away from both endpoints."""
    if not point_on_segment(point, start, end, tolerance):
        return False
    return (
        _distance(point, start) > tolerance
        and _distance(point, end) > tolerance
    )


def branch_joint_point(through_obj, branch_obj, tolerance=DEFAULT_POINT_TOLERANCE):
    """Return the branch endpoint that lands on the selected through tube.

    A branch must end at the through tube. The through tube may itself end at
    that point (corner) or continue through it (interior T-joint).
    """
    through_start, through_end = _end_xyz(through_obj)
    branch_start, branch_end = _end_xyz(branch_obj)
    candidates = []
    for point in (branch_start, branch_end):
        if point_on_segment(point, through_start, through_end, tolerance):
            key = _point_key_xyz(point)
            if all(_point_key_xyz(existing) != key for existing in candidates):
                candidates.append(point)

    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        raise ValueError(
            "The selected branch lies along the through tube. "
            "Through Selected requires a branch that ends at the through tube."
        )

    # No branch endpoint lands on the through tube. If the through tube has an
    # endpoint inside the branch, the requested ordering would require cutting
    # the branch in its middle, which an end cope cannot represent.
    for point in (through_start, through_end):
        if point_strictly_inside_segment(point, branch_start, branch_end, tolerance):
            raise ValueError(
                "The second tube continues through the intersection instead of ending there. "
                "If the first tube is to stay through, split the second tube at the joint "
                "into branch pieces, then select the through tube first."
            )

    # Also give the useful crossing message for two continuous segments that
    # intersect away from all four endpoints.
    crossing = segment_intersection_point(
        through_start, through_end, branch_start, branch_end, tolerance
    )
    if crossing is not None:
        raise ValueError(
            "Both selected tubes continue through the intersection. "
            "A tube-frame through joint needs one continuous tube and branch tube(s) "
            "ending at it. Split the branch at the intersection and select the main tube first."
        )

    raise ValueError(
        "The selected tubes must share exactly one valid joint; "
        "the selected branch does not end on the selected through tube."
    )


def segment_intersection_point(a0, a1, b0, b1, tolerance=DEFAULT_POINT_TOLERANCE):
    """Return an approximate intersection point for two finite 3D segments."""
    u = _sub(a1, a0)
    v = _sub(b1, b0)
    w = _sub(a0, b0)
    aa = _dot(u, u)
    bb = _dot(u, v)
    cc = _dot(v, v)
    dd = _dot(u, w)
    ee = _dot(v, w)
    denom = aa * cc - bb * bb
    if aa <= 1e-24 or cc <= 1e-24:
        return None
    if abs(denom) <= 1e-18:
        return None
    s = (bb * ee - cc * dd) / denom
    t = (aa * ee - bb * dd) / denom
    if s < -tolerance or s > 1.0 + tolerance or t < -tolerance or t > 1.0 + tolerance:
        return None
    p = _add(a0, _mul(u, s))
    q = _add(b0, _mul(v, t))
    if _distance(p, q) > tolerance:
        return None
    return _mul(_add(p, q), 0.5)


def selected_joint_point(objects, precision=6):
    """Resolve one common physical connection point for selected straight members.

    Unlike the old helper this accepts endpoint-to-interior T-joints as well as
    ordinary endpoint-to-endpoint joints.
    """
    objects = list(objects or ())
    if len(objects) < 2:
        raise ValueError("Select at least two ForgeCAD members.")
    first = objects[0]
    points = []
    for other in objects[1:]:
        first_start, first_end = _end_xyz(first)
        other_start, other_end = _end_xyz(other)
        candidates = []
        for point in (first_start, first_end):
            if point_on_segment(point, other_start, other_end):
                candidates.append(point)
        for point in (other_start, other_end):
            if point_on_segment(point, first_start, first_end):
                if all(_point_key_xyz(point) != _point_key_xyz(x) for x in candidates):
                    candidates.append(point)
        if len(candidates) != 1:
            raise ValueError("The selected tubes must share exactly one unambiguous joint point.")
        points.append(candidates[0])
    keys = {_point_key_xyz(point, precision) for point in points}
    if len(keys) != 1:
        raise ValueError("All selected tubes must meet at the same joint point.")
    return next(iter(keys))


def selected_through_request(objects, precision=6):
    """Resolve first-selected through tube, branch tubes, and their joint point."""
    objects = list(objects or ())
    if len(objects) < 2:
        raise ValueError(
            "Select the tube that stays through first, then one or more branch tubes."
        )

    ids = []
    for obj in objects:
        ident = _layout_id(obj)
        if not ident:
            raise ValueError(
                "Every selected tube must be a generated ForgeCAD member with a SourceLayoutID."
            )
        if ident in ids:
            raise ValueError("Select each tube only once.")
        ids.append(ident)

    through_obj = objects[0]
    points = [branch_joint_point(through_obj, branch) for branch in objects[1:]]
    keys = {_point_key_xyz(point, precision) for point in points}
    if len(keys) != 1:
        raise ValueError("All selected branch tubes must meet the through tube at the same joint.")

    return next(iter(keys)), ids[0], tuple(ids[1:])


def replace_branch_pairs(existing_pairs, through_id, branch_ids):
    """Point selected branches at the selected through tube."""
    through_id = str(through_id or "").strip()
    branches = tuple(str(value or "").strip() for value in branch_ids)
    if not through_id or not branches:
        raise ValueError("Through Selected requires one through tube and at least one branch.")
    if any(not value or value == through_id for value in branches):
        raise ValueError("Branch tubes must be different from the through tube.")
    if len(set(branches)) != len(branches):
        raise ValueError("Branch tubes must be unique.")

    branch_set = set(branches)
    kept = []
    for pair in existing_pairs or ():
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError("A stored through pair is malformed.")
        source = str(pair[0] or "").strip()
        target = str(pair[1] or "").strip()
        if not source or not target or source == target:
            raise ValueError("A stored through pair is malformed.")
        value = (source, target)
        if source not in branch_set and value not in kept:
            kept.append(value)

    for branch in branches:
        value = (branch, through_id)
        if value not in kept:
            kept.append(value)
    return tuple(kept)


def remove_source_pairs(existing_pairs, source_ids):
    """Remove generic direct-cope records for selected source members."""
    sources = {str(value or "").strip() for value in source_ids}
    result = []
    for pair in existing_pairs or ():
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError("A stored cope pair is malformed.")
        source = str(pair[0] or "").strip()
        target = str(pair[1] or "").strip()
        if not source or not target or source == target:
            raise ValueError("A stored cope pair is malformed.")
        value = (source, target)
        if source not in sources and value not in result:
            result.append(value)
    return tuple(result)


def validate_primary_compatibility(saved_treatment, selected_ids):
    """Reject old primary treatments that conflict with selected direct members."""
    if saved_treatment is None:
        return
    mode, primary_ids = saved_treatment
    mode = str(getattr(mode, "value", mode) or "").strip()
    primary_ids = tuple(str(value or "").strip() for value in (primary_ids or ()))
    selected = set(str(value or "").strip() for value in selected_ids)

    if mode in ("", "auto"):
        return
    if mode == "both_coped":
        if not primary_ids:
            raise ValueError(
                "This joint has a legacy miter without saved member IDs. Clear that miter first."
            )
        if selected.intersection(primary_ids):
            raise ValueError(
                "One selected tube is already part of this joint's miter. "
                "Clear that miter first, then use Through Selected."
            )
        return
    if mode in ("member_through", "through_pair"):
        raise ValueError(
            "This joint still uses a legacy joint-wide Through treatment. "
            "Set it to Automatic once in Inspect Joint before using the direct Through command."
        )
