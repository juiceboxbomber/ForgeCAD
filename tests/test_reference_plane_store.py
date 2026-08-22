"""Tests for persistent ForgeCAD reference-plane storage."""

import sys
import types
from types import SimpleNamespace


sys.modules[
    "FreeCAD"
] = types.ModuleType(
    "FreeCAD"
)

sys.modules[
    "FreeCADGui"
] = types.ModuleType(
    "FreeCADGui"
)

sys.modules[
    "Part"
] = types.ModuleType(
    "Part"
)


from forgecad.geometry import (
    ReferencePlane,
    ReferencePlaneOrientation,
)
from forgecad.adapters.freecad import (
    reference_plane_store as module,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


class FakeObject:
    def __init__(
        self,
        name,
        object_type="",
    ):
        self.Name = name
        self.Label = name
        self.TypeId = object_type
        self._properties = {}

        if object_type == "Part::Feature":
            self.Shape = None

    def addProperty(
        self,
        property_type,
        name,
        group,
    ):
        self._properties[
            name
        ] = (
            property_type,
            group,
        )

        if property_type == "App::PropertyEnumeration":
            setattr(
                self,
                name,
                "",
            )

        elif property_type == "App::PropertyLength":
            setattr(
                self,
                name,
                0.0,
            )

        else:
            setattr(
                self,
                name,
                "",
            )

    def setEditorMode(
        self,
        property_name,
        mode,
    ):
        pass


class FakeGroup(
    FakeObject
):
    def __init__(
        self,
        name,
        object_type="",
    ):
        super().__init__(
            name,
            object_type=object_type,
        )

        self.Group = []

    def addObject(
        self,
        obj,
    ):
        if obj not in self.Group:
            self.Group.append(
                obj
            )

    def removeObject(
        self,
        obj,
    ):
        if obj in self.Group:
            self.Group.remove(
                obj
            )


class FakeDocument:
    def __init__(
        self,
    ):
        self.objects = {}
        self.recompute_count = 0

    def getObject(
        self,
        name,
    ):
        return self.objects.get(
            name
        )

    def addObject(
        self,
        object_type,
        name,
    ):
        if object_type in (
            "App::DocumentObjectGroup",
            "App::DocumentObjectGroupPython",
        ):
            obj = FakeGroup(
                name,
                object_type=object_type,
            )

        else:
            obj = FakeObject(
                name,
                object_type=object_type,
            )

        self.objects[
            name
        ] = obj

        return obj

    def removeObject(
        self,
        name,
    ):
        self.objects.pop(
            name,
            None,
        )

    def recompute(
        self,
    ):
        self.recompute_count += 1


def test_project_tree_contains_reference_geometry_group():
    document = FakeDocument()

    groups = (
        initialize_project_tree(
            document
        )
    )

    assert (
        "Reference Geometry"
        in groups
    )

    group = groups[
        "Reference Geometry"
    ]

    assert group.Name == (
        "ForgeCADReferenceGeometry"
    )

    assert group.Label == (
        "Reference Geometry"
    )


def test_reference_geometry_group_is_child_of_project_root():
    document = FakeDocument()

    groups = (
        initialize_project_tree(
            document
        )
    )

    root = document.getObject(
        "ForgeCADProject"
    )

    assert groups[
        "Reference Geometry"
    ] in root.Group


def test_reference_plane_object_is_shape_bearing_part_feature():
    document = FakeDocument()

    obj = module.create_reference_plane_object(
        document
    )

    assert obj.TypeId == (
        "Part::Feature"
    )

    assert hasattr(
        obj,
        "Shape",
    )


def test_save_reference_plane_creates_persistent_object():
    document = FakeDocument()

    plane = ReferencePlane(
        name="Roof Plane",
        orientation=ReferencePlaneOrientation.XY,
        offset=1200.0,
    )

    obj = module.save_reference_plane(
        document,
        plane,
    )

    assert obj.ReferenceName == (
        "Roof Plane"
    )

    assert str(
        obj.Orientation
    ) == "XY"

    assert float(
        obj.Offset
    ) == 1200.0

    assert obj.Label == (
        "Roof Plane"
    )


def test_saved_plane_is_added_to_reference_geometry_group():
    document = FakeDocument()

    obj = module.save_reference_plane(
        document,
        ReferencePlane(
            name="Center Plane",
            orientation="XZ",
            offset=0.0,
        ),
    )

    group = document.getObject(
        "ForgeCADReferenceGeometry"
    )

    assert obj in group.Group


def test_reference_plane_round_trip():
    document = FakeDocument()

    module.save_reference_plane(
        document,
        ReferencePlane(
            name="Front Hoop Plane",
            orientation="YZ",
            offset=900.0,
        ),
    )

    planes = module.load_reference_planes(
        document
    )

    assert planes == (
        ReferencePlane(
            name="Front Hoop Plane",
            orientation=ReferencePlaneOrientation.YZ,
            offset=900.0,
        ),
    )


def test_find_reference_plane_object_by_name():
    document = FakeDocument()

    first = module.save_reference_plane(
        document,
        ReferencePlane(
            name="Center Plane",
            orientation="XZ",
            offset=0.0,
        ),
    )

    module.save_reference_plane(
        document,
        ReferencePlane(
            name="Roof Plane",
            orientation="XY",
            offset=1200.0,
        ),
    )

    assert (
        module.find_reference_plane_object(
            document,
            "Center Plane",
        )
        is first
    )


def test_missing_reference_geometry_group_is_read_only_empty():
    document = FakeDocument()

    assert (
        module.reference_plane_objects(
            document
        )
        == ()
    )

    assert (
        document.getObject(
            "ForgeCADReferenceGeometry"
        )
        is None
    )


def test_invalid_object_is_rejected():
    invalid = SimpleNamespace()

    try:
        module.reference_plane_from_object(
            invalid
        )
    except ValueError as error:
        assert "not a ForgeCAD reference plane" in str(
            error
        )
    else:
        raise AssertionError(
            "Expected invalid object to be rejected."
        )
