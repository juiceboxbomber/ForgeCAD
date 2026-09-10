"""Pure selection helpers for ForgeCAD's direct Clear Selected command."""

from forgecad.services.selected_through import selected_joint_point


def _layout_id(obj):
    return str(getattr(obj, "SourceLayoutID", "") or "").strip()


def selected_clear_request(objects, precision=6):
    """Resolve two/three selected members and their physical joint point."""
    objects = list(objects or ())
    if len(objects) not in (2, 3):
        raise ValueError(
            "Select two tubes to clear a miter/cope/through operation, or select "
            "one source/through tube plus two related tubes to clear both relationships."
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
    return selected_joint_point(objects, precision=precision), tuple(ids)


def _normalized_pairs(pairs, label):
    result = []
    for pair in pairs or ():
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError("A stored " + label + " pair is malformed.")
        source = str(pair[0] or "").strip()
        target = str(pair[1] or "").strip()
        if not source or not target or source == target:
            raise ValueError("A stored " + label + " pair is malformed.")
        value = (source, target)
        if value not in result:
            result.append(value)
    return result


def clear_selected_operation_plan(
    saved_treatment,
    existing_cope_pairs,
    selected_ids,
    joint_member_ids=(),
    existing_through_pairs=(),
):
    """Plan a selection-first clear without deleting unrelated operations.

    Returns:
        clear_primary,
        remaining_cope_pairs,
        removed_cope_pairs,
        remaining_through_pairs,
        removed_through_pairs
    """
    selected_ids = tuple(str(value or "").strip() for value in selected_ids)
    if len(selected_ids) not in (2, 3) or any(not value for value in selected_ids):
        raise ValueError("Clear Selected requires two or three valid member IDs.")
    if len(set(selected_ids)) != len(selected_ids):
        raise ValueError("Clear Selected member IDs must be unique.")

    first_id = selected_ids[0]
    following_ids = set(selected_ids[1:])
    copes = _normalized_pairs(existing_cope_pairs, "cope")
    throughs = _normalized_pairs(existing_through_pairs, "through")

    removed_copes = [
        pair for pair in copes
        if pair[0] == first_id and pair[1] in following_ids
    ]
    removed_throughs = [
        pair for pair in throughs
        if pair[1] == first_id and pair[0] in following_ids
    ]

    # Migration compatibility for Phase 3: Through Selected was stored in the
    # generic cope list as branch -> through. Allow Through-order clearing of
    # those old records only when no dedicated through record exists.
    legacy_through_copes = []
    if not removed_throughs and not removed_copes:
        legacy_through_copes = [
            pair for pair in copes
            if pair[1] == first_id and pair[0] in following_ids
        ]
        removed_copes.extend(legacy_through_copes)

    remaining_copes = [pair for pair in copes if pair not in removed_copes]
    remaining_throughs = [pair for pair in throughs if pair not in removed_throughs]

    clear_primary = False
    if saved_treatment is not None:
        mode, primary_ids = saved_treatment
        mode = str(getattr(mode, "value", mode) or "").strip()
        primary_ids = tuple(str(value or "").strip() for value in (primary_ids or ()))
        if mode == "both_coped" and len(selected_ids) == 2:
            if len(primary_ids) == 2:
                clear_primary = set(primary_ids) == set(selected_ids)
            elif not primary_ids:
                joint_ids = {
                    str(value or "").strip()
                    for value in (joint_member_ids or ())
                    if str(value or "").strip()
                }
                clear_primary = joint_ids == set(selected_ids)

    if not clear_primary and not removed_copes and not removed_throughs:
        raise ValueError(
            "No matching selected miter, cope, or through relationship is saved at this joint."
        )

    return (
        clear_primary,
        tuple(remaining_copes),
        tuple(removed_copes),
        tuple(remaining_throughs),
        tuple(removed_throughs),
    )


def clear_selected_plan(
    saved_treatment,
    existing_pairs,
    selected_ids,
    joint_member_ids=(),
):
    """Backward-compatible Phase 2/3 clear planner.

    Dedicated Through records were introduced in Phase 4. Older callers and
    tests still receive the original three-item result.
    """
    (
        clear_primary,
        remaining_copes,
        removed_copes,
        _remaining_throughs,
        _removed_throughs,
    ) = clear_selected_operation_plan(
        saved_treatment,
        existing_pairs,
        selected_ids,
        joint_member_ids,
        (),
    )
    return clear_primary, remaining_copes, removed_copes
