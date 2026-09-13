"""Geometric proximity helpers shared by ForgeCAD joint services."""

POINT_TOLERANCE = 1e-6


def nodes_coincident(first, second, tolerance=POINT_TOLERANCE) -> bool:
    """Return True when two node-like XYZ points occupy the same location."""
    if first is None or second is None:
        return False
    tolerance = float(tolerance)
    return (
        abs(float(first.x) - float(second.x)) <= tolerance
        and abs(float(first.y) - float(second.y)) <= tolerance
        and abs(float(first.z) - float(second.z)) <= tolerance
    )
