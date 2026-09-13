"""Strict validation for persisted selection-first member relationship pairs."""


def normalized_pairs(pairs):
    """Return unique directed member-ID pairs, rejecting malformed input.

    The order supplied by the caller is preserved.  This validator is used by
    persistence writes for both Cope Selected and Through Selected so invalid
    records are rejected before a FreeCAD document is changed.
    """
    result = []
    for pair in pairs:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError(
                "Each fabrication relationship must contain two member IDs."
            )
        first, second = (str(value or "").strip() for value in pair)
        if not first or not second or first == second:
            raise ValueError(
                "A fabrication relationship requires two different, non-empty member IDs."
            )
        value = (first, second)
        if value not in result:
            result.append(value)
    return tuple(result)
