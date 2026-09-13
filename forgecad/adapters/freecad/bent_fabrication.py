"""Fabrication operations applied directly to ForgeCAD bent-tube solids."""


def _numeric(value) -> float:
    return float(getattr(value, "Value", value))


def _normalized_xyz(value):
    x, y, z = float(value.x), float(value.y), float(value.z)
    length = (x * x + y * y + z * z) ** 0.5
    if length <= 1e-12:
        raise ValueError("Bent-tube endpoint direction cannot be zero.")
    return (x / length, y / length, z / length)


def _miter_cutter_size(shape, profile) -> float:
    outside_diameter = float(profile.outside_diameter)
    dimensions = [outside_diameter, 1.0]
    bound_box = getattr(shape, "BoundBox", None)
    if bound_box is not None:
        for name in ("XLength", "YLength", "ZLength"):
            try:
                dimensions.append(_numeric(getattr(bound_box, name)))
            except (AttributeError, TypeError, ValueError):
                pass
    return max(dimensions) * 4.0


def _point_vector(point):
    import FreeCAD
    return FreeCAD.Vector(float(point.x), float(point.y), float(point.z))


def _fuse_endpoint_extension(
    shape,
    inner_point,
    direction,
    extension_mm,
    profile,
    outward_sign,
):
    """Fuse straight hollow stock onto one bent endpoint before trimming."""
    extension_mm = float(getattr(extension_mm, "Value", extension_mm))
    if extension_mm <= 1e-9:
        return shape

    import FreeCAD
    from forgecad.adapters.freecad.member_object import build_tube_shape

    dx, dy, dz = _normalized_xyz(direction)
    outside_diameter = float(profile.outside_diameter)
    overlap = min(
        max(outside_diameter * 0.02, 0.05),
        max(extension_mm * 0.25, 0.05),
    )

    base = _point_vector(inner_point)
    outward = FreeCAD.Vector(
        dx * float(outward_sign),
        dy * float(outward_sign),
        dz * float(outward_sign),
    )
    outer = FreeCAD.Vector(
        base.x + outward.x * extension_mm,
        base.y + outward.y * extension_mm,
        base.z + outward.z * extension_mm,
    )
    overlap_point = FreeCAD.Vector(
        base.x - outward.x * overlap,
        base.y - outward.y * overlap,
        base.z - outward.z * overlap,
    )

    extension_shape, _ = build_tube_shape(overlap_point, outer, profile)
    fused = shape.fuse(extension_shape)
    try:
        fused = fused.removeSplitter()
    except Exception:
        pass
    return fused


def _bent_tube_definition(
    obj,
):
    """Return the current domain BentTube represented by a FreeCAD object."""

    proxy = getattr(
        obj,
        "Proxy",
        None,
    )

    if (
        proxy is None
        or not hasattr(
            proxy,
            "_tube_from_properties",
        )
    ):
        return None

    try:
        return proxy._tube_from_properties(
            obj
        )
    except Exception:
        return None


def _endpoint_run_lengths(
    obj,
):
    """Return current first/last straight-run lengths when available."""

    tube = _bent_tube_definition(
        obj
    )

    if (
        tube is None
        or not getattr(
            tube,
            "straight_runs",
            (),
        )
    ):
        return (
            None,
            None,
        )

    runs = tuple(
        tube.straight_runs
    )

    return (
        float(
            runs[0].length_mm
        ),
        float(
            runs[-1].length_mm
        ),
    )


def _local_miter_cutter_size(
    profile,
    extension_mm,
    straight_run_length=None,
) -> float:
    """
    Return a cutter size large enough for one end, but local to that end.

    Straight-member miter cutters may safely span an entire member because a
    straight tube lies on one side of the miter plane. A bent tube can cross
    the same plane elsewhere, so using the full bent-tube bounding box can cut
    away unrelated curved geometry. The bent cutter is therefore sized from
    the local tube diameter and endpoint extension only.

    The optional straight-run length is used only as a sanity floor/ceiling
    hint; the cutter is never made smaller than the stock required to trim the
    endpoint extension and complete tube cross-section.
    """

    outside_diameter = float(
        profile.outside_diameter
    )

    extension_mm = max(
        0.0,
        _numeric(
            extension_mm
        ),
    )

    required = max(
        outside_diameter * 6.0,
        (
            extension_mm
            + outside_diameter * 2.0
        )
        * 2.0,
    )

    if (
        straight_run_length is None
        or straight_run_length <= 0.0
    ):
        return required

    # Keep the cutter local whenever there is enough straight tangent length.
    # Do not shrink below required: incomplete trimming would leave a detached
    # extension tail beyond the miter plane.
    preferred_local_limit = max(
        outside_diameter * 6.0,
        float(
            straight_run_length
        )
        * 0.75,
    )

    return max(
        required,
        min(
            required * 1.5,
            preferred_local_limit,
        ),
    )

def apply_bent_miter_shape(
    obj,
    shape,
    profile,
    centerline=None,
):
    """
    Add endpoint stock and apply saved planar miters locally.

    Bent members use an endpoint-local keep point and cutter. After each cut,
    discard any disconnected outside fragment so temporary extension stock
    cannot remain as a separate remnant.
    """

    from forgecad.adapters.freecad.member_notch import (
        ensure_notch_properties,
    )
    from forgecad.adapters.freecad.miter_geometry import (
        miter_tube_shape,
    )
    from forgecad.adapters.freecad.notch_geometry import (
        primary_cope_component,
    )

    ensure_notch_properties(
        obj
    )

    has_solved_centerline = (
        centerline is not None
        and hasattr(
            centerline,
            "start_point",
        )
        and hasattr(
            centerline,
            "end_point",
        )
        and hasattr(
            centerline,
            "end_direction",
        )
    )

    start_point = (
        centerline.start_point
        if has_solved_centerline
        else getattr(
            obj,
            "StartPoint",
        )
    )

    start_direction = getattr(
        obj,
        "InitialDirection",
    )

    start_extension = getattr(
        obj,
        "StartExtension",
        0.0,
    )

    end_extension = getattr(
        obj,
        "EndExtension",
        0.0,
    )

    start_run_length, end_run_length = (
        _endpoint_run_lengths(
            obj
        )
    )

    shape = _fuse_endpoint_extension(
        shape,
        start_point,
        start_direction,
        start_extension,
        profile,
        outward_sign=-1.0,
    )

    if has_solved_centerline:
        shape = _fuse_endpoint_extension(
            shape,
            centerline.end_point,
            centerline.end_direction,
            end_extension,
            profile,
            outward_sign=1.0,
        )

    if bool(
        getattr(
            obj,
            "StartMiterEnabled",
            False,
        )
    ):
        start_cutter_size = (
            _local_miter_cutter_size(
                profile,
                start_extension,
                start_run_length,
            )
        )

        shape = miter_tube_shape(
            tube_shape=shape,
            plane_point=(
                obj.StartMiterPlanePoint
            ),
            plane_normal=(
                obj.StartMiterPlaneNormal
            ),
            keep_point=(
                obj.StartMiterKeepPoint
            ),
            cutter_size=(
                start_cutter_size
            ),
        )

        shape = primary_cope_component(
            shape,
            obj.StartMiterKeepPoint,
        )

    if bool(
        getattr(
            obj,
            "EndMiterEnabled",
            False,
        )
    ):
        end_cutter_size = (
            _local_miter_cutter_size(
                profile,
                end_extension,
                end_run_length,
            )
        )

        shape = miter_tube_shape(
            tube_shape=shape,
            plane_point=(
                obj.EndMiterPlanePoint
            ),
            plane_normal=(
                obj.EndMiterPlaneNormal
            ),
            keep_point=(
                obj.EndMiterKeepPoint
            ),
            cutter_size=(
                end_cutter_size
            ),
        )

        shape = primary_cope_component(
            shape,
            obj.EndMiterKeepPoint,
        )

    return shape
