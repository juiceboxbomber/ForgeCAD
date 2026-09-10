"""Pure presentation helpers for ForgeCAD joint review."""


def _text(value):
    return str(value or "").strip()


def _mode_value(value):
    return _text(getattr(value, "value", value))


def display_name(layout_id, names):
    """Return a readable persistent member identity."""
    ident = _text(layout_id)
    if not ident:
        return "—"
    label = _text((names or {}).get(ident, ""))
    return label or ident


def fabrication_rows(saved_treatment, cope_pairs=(), through_pairs=(), names=None):
    """Return read-only rows describing saved fabrication at one joint.

    Each row is (operation, member, other/details). Selection-first cope and
    through records are additive to the primary treatment, so all are shown.
    """
    names = names or {}
    rows = []

    if saved_treatment is None:
        mode = "auto"
        primary_ids = ()
    else:
        try:
            raw_mode, raw_ids = saved_treatment
        except (TypeError, ValueError) as error:
            raise ValueError("Saved joint treatment is malformed.") from error
        mode = _mode_value(raw_mode)
        primary_ids = tuple(_text(value) for value in (raw_ids or ()) if _text(value))

    if mode in ("both_coped", "both_mitered"):
        first = display_name(primary_ids[0], names) if len(primary_ids) >= 1 else "Saved miter"
        second = display_name(primary_ids[1], names) if len(primary_ids) >= 2 else "Pair not identified"
        rows.append(("Miter", first, second))
    elif mode == "member_through":
        member = display_name(primary_ids[0], names) if primary_ids else "Saved member"
        rows.append(("Legacy Through", member, "Primary joint treatment"))
    elif mode == "through_pair":
        first = display_name(primary_ids[0], names) if len(primary_ids) >= 1 else "Saved member"
        second = display_name(primary_ids[1], names) if len(primary_ids) >= 2 else "Pair not identified"
        rows.append(("Legacy Through Pair", first, second))
    elif mode and mode != "auto":
        rows.append((mode.replace("_", " ").title(), "Saved primary treatment", ""))

    seen = set()
    for pair in cope_pairs or ():
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError("Saved cope relationship is malformed.")
        source, target = (_text(pair[0]), _text(pair[1]))
        if not source or not target or source == target:
            raise ValueError("Saved cope relationship is malformed.")
        key = ("Cope", source, target)
        if key in seen:
            continue
        seen.add(key)
        rows.append(("Cope", display_name(source, names), display_name(target, names)))

    for pair in through_pairs or ():
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError("Saved through relationship is malformed.")
        branch, through = (_text(pair[0]), _text(pair[1]))
        if not branch or not through or branch == through:
            raise ValueError("Saved through relationship is malformed.")
        key = ("Through", branch, through)
        if key in seen:
            continue
        seen.add(key)
        rows.append((
            "Through",
            display_name(through, names),
            "Branch: " + display_name(branch, names),
        ))

    if not rows:
        rows.append(("Automatic", "—", "No manual fabrication operation saved"))

    return tuple(rows)
