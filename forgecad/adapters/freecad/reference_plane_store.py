"""Persistent FreeCAD storage for ForgeCAD reference planes."""

from forgecad.geometry import (
    ReferencePlane,
    ReferencePlaneOrientation,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


REFERENCE_PLANE_OBJECT_NAME = (
    "ForgeCADReferencePlane"
)

PROPERTY_GROUP = (
    "ForgeCAD Reference Plane"
)


def ensure_reference_plane_properties(
    obj,
):
    """Ensure a FreeCAD object contains reference-plane metadata."""

    if not hasattr(
        obj,
        "ReferenceName",
    ):
        obj.addProperty(
            "App::PropertyString",
            "ReferenceName",
            PROPERTY_GROUP,
        )

    if not hasattr(
        obj,
        "Orientation",
    ):
        obj.addProperty(
            "App::PropertyEnumeration",
            "Orientation",
            PROPERTY_GROUP,
        )

        obj.Orientation = [
            "XY",
            "XZ",
            "YZ",
        ]

    if not hasattr(
        obj,
        "Offset",
    ):
        obj.addProperty(
            "App::PropertyLength",
            "Offset",
            PROPERTY_GROUP,
        )

    for property_name in (
        "ReferenceName",
        "Orientation",
        "Offset",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj


def is_reference_plane_object(
    obj,
):
    """Return True for a persistent ForgeCAD reference-plane object."""

    return all(
        hasattr(
            obj,
            property_name,
        )
        for property_name in (
            "ReferenceName",
            "Orientation",
            "Offset",
        )
    )


def existing_reference_geometry_group(
    document,
):
    """Return the Reference Geometry group without creating it."""

    if document is None:
        return None

    return document.getObject(
        "ForgeCADReferenceGeometry"
    )


def reference_plane_objects(
    document,
):
    """Return all persistent ForgeCAD reference-plane objects."""

    group = existing_reference_geometry_group(
        document
    )

    if group is None:
        return ()

    return tuple(
        obj
        for obj in getattr(
            group,
            "Group",
            (),
        )
        if is_reference_plane_object(
            obj
        )
    )


def reference_plane_from_object(
    obj,
):
    """Return a domain ReferencePlane reconstructed from a FreeCAD object."""

    if not is_reference_plane_object(
        obj
    ):
        raise ValueError(
            "Object is not a ForgeCAD reference plane."
        )

    orientation = str(
        obj.Orientation
    ).strip()

    offset_value = (
        getattr(
            obj.Offset,
            "Value",
            obj.Offset,
        )
    )

    return ReferencePlane(
        name=str(
            obj.ReferenceName
        ).strip(),
        orientation=ReferencePlaneOrientation(
            orientation
        ),
        offset=float(
            offset_value
        ),
    )


def create_reference_plane_object(
    document,
):
    """
    Create one persistent, shape-bearing ForgeCAD reference-plane object.

    Part::Feature is intentional: reference planes carry both ForgeCAD
    metadata and visible selectable planar geometry.
    """

    groups = initialize_project_tree(
        document
    )

    obj = document.addObject(
        "Part::Feature",
        REFERENCE_PLANE_OBJECT_NAME,
    )

    ensure_reference_plane_properties(
        obj
    )

    groups[
        "Reference Geometry"
    ].addObject(
        obj
    )

    return obj


def save_reference_plane(
    document,
    plane,
):
    """
    Persist one ForgeCAD ReferencePlane in the active document.

    A new object is created for each call. Name and geometric uniqueness are
    handled separately by higher-level command/UI logic.
    """

    if document is None:
        raise ValueError(
            "Reference plane requires an active document."
        )

    if not isinstance(
        plane,
        ReferencePlane,
    ):
        raise TypeError(
            "save_reference_plane requires a ReferencePlane."
        )

    obj = create_reference_plane_object(
        document
    )

    obj.ReferenceName = (
        plane.name
    )

    obj.Orientation = (
        plane.orientation.value
    )

    obj.Offset = float(
        plane.offset
    )

    obj.Label = (
        plane.name
    )

    document.recompute()

    return obj


def load_reference_planes(
    document,
):
    """Return all persistent reference planes as domain objects."""

    return tuple(
        reference_plane_from_object(
            obj
        )
        for obj in reference_plane_objects(
            document
        )
    )


def find_reference_plane_object(
    document,
    name,
):
    """Return a reference-plane object by its user-facing name."""

    requested_name = str(
        name
    ).strip()

    if not requested_name:
        return None

    for obj in reference_plane_objects(
        document
    ):
        if (
            str(
                obj.ReferenceName
            ).strip()
            == requested_name
        ):
            return obj

    return None


def find_reference_plane_at_location(
    document,
    orientation,
    offset,
    tolerance=1e-6,
):
    """Return an existing plane with the same orientation and offset."""

    requested_orientation = str(
        getattr(
            orientation,
            "value",
            orientation,
        )
    ).strip()

    requested_offset = float(
        offset
    )

    for obj in reference_plane_objects(
        document
    ):
        existing_orientation = str(
            obj.Orientation
        ).strip()

        existing_offset_value = getattr(
            obj.Offset,
            "Value",
            obj.Offset,
        )

        existing_offset = float(
            existing_offset_value
        )

        if (
            existing_orientation
            == requested_orientation
            and abs(
                existing_offset
                - requested_offset
            )
            <= tolerance
        ):
            return obj

    return None
