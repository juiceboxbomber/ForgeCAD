"""Persistent FreeCAD storage for ForgeCAD bender tooling."""

from forgecad.fabrication import (
    BendMarkReference,
    BenderLibrary,
    BenderTooling,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


STORE_OBJECT_NAME = "ForgeCADBenderLibrary"


def _ensure_store_properties(
    obj,
):
    """Ensure persistent bender-library properties exist."""

    property_definitions = (
        (
            "App::PropertyStringList",
            "ToolingNames",
        ),
        (
            "App::PropertyStringList",
            "CenterlineRadii",
        ),
        (
            "App::PropertyStringList",
            "MarkReferences",
        ),
        (
            "App::PropertyStringList",
            "MarkOffsets",
        ),
        (
            "App::PropertyStringList",
            "AngleCompensations",
        ),
        (
            "App::PropertyString",
            "ActiveToolingName",
        ),
    )

    for (
        property_type,
        property_name,
    ) in property_definitions:
        if hasattr(
            obj,
            property_name,
        ):
            continue

        obj.addProperty(
            property_type,
            property_name,
            "ForgeCAD Bender Library",
        )

    for property_name in (
        "ToolingNames",
        "CenterlineRadii",
        "MarkReferences",
        "MarkOffsets",
        "AngleCompensations",
        "ActiveToolingName",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj


def get_or_create_bender_store(
    document,
):
    """Return the persistent bender-library storage object."""

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    groups = initialize_project_tree(
        document
    )

    settings_group = groups[
        "Settings"
    ]

    obj = document.getObject(
        STORE_OBJECT_NAME
    )

    if obj is None:
        obj = document.addObject(
            "App::FeaturePython",
            STORE_OBJECT_NAME,
        )
        obj.Label = (
            "Bender Tooling Library"
        )

    _ensure_store_properties(
        obj
    )

    if obj not in settings_group.Group:
        settings_group.addObject(
            obj
        )

    return obj


def save_bender_library(
    document,
    library,
):
    """Persist one BenderLibrary into a FreeCAD document."""

    if not isinstance(
        library,
        BenderLibrary,
    ):
        raise TypeError(
            "library must be a BenderLibrary instance."
        )

    obj = get_or_create_bender_store(
        document
    )

    tooling_items = tuple(
        library.get(
            name
        )
        for name in library.names
    )

    obj.ToolingNames = [
        tooling.name
        for tooling in tooling_items
    ]

    obj.CenterlineRadii = [
        repr(
            tooling.centerline_radius_mm
        )
        for tooling in tooling_items
    ]

    obj.MarkReferences = [
        tooling.mark_reference.value
        for tooling in tooling_items
    ]

    obj.MarkOffsets = [
        repr(
            tooling.mark_offset_mm
        )
        for tooling in tooling_items
    ]

    obj.AngleCompensations = [
        repr(
            tooling.angle_compensation_degrees
        )
        for tooling in tooling_items
    ]

    obj.ActiveToolingName = (
        library.active_name
        or ""
    )

    document.recompute()

    return obj


def load_bender_library(
    document,
) -> BenderLibrary:
    """Load the project's persisted BenderLibrary."""

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    obj = document.getObject(
        STORE_OBJECT_NAME
    )

    if obj is None:
        return BenderLibrary()

    _ensure_store_properties(
        obj
    )

    names = list(
        obj.ToolingNames
    )
    radii = list(
        obj.CenterlineRadii
    )
    references = list(
        obj.MarkReferences
    )
    offsets = list(
        obj.MarkOffsets
    )
    compensations = list(
        obj.AngleCompensations
    )

    lengths = {
        len(
            names
        ),
        len(
            radii
        ),
        len(
            references
        ),
        len(
            offsets
        ),
        len(
            compensations
        ),
    }

    if len(
        lengths
    ) != 1:
        raise ValueError(
            "Persisted bender tooling data is inconsistent."
        )

    library = BenderLibrary()

    for (
        name,
        radius,
        reference,
        offset,
        compensation,
    ) in zip(
        names,
        radii,
        references,
        offsets,
        compensations,
    ):
        library.add(
            BenderTooling(
                name=name,
                centerline_radius_mm=float(
                    radius
                ),
                mark_reference=BendMarkReference(
                    reference
                ),
                mark_offset_mm=float(
                    offset
                ),
                angle_compensation_degrees=float(
                    compensation
                ),
            )
        )

    active_name = str(
        obj.ActiveToolingName
    ).strip()

    if active_name:
        if active_name not in library.names:
            raise ValueError(
                "Persisted active bender tooling does not exist."
            )

        library.set_active(
            active_name
        )

    return library
