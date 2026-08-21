"""Tests for persistent FreeCAD joint-constraint storage."""

import importlib
import sys
import types

from forgecad.fabrication.joint_constraint import (
    CollinearThroughConstraint,
    JointConstraintKind,
)
from forgecad.geometry.point import Point3D


class FakeVector:
    def __init__(
        self,
        x=0.0,
        y=0.0,
        z=0.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


fake_freecad = sys.modules.get(
    "FreeCAD"
)

if fake_freecad is None:
    fake_freecad = types.ModuleType(
        "FreeCAD"
    )

    sys.modules[
        "FreeCAD"
    ] = fake_freecad

fake_freecad.Vector = FakeVector


fake_part = sys.modules.get(
    "Part"
)

if fake_part is None:
    fake_part = types.ModuleType(
        "Part"
    )

    sys.modules[
        "Part"
    ] = fake_part


class FakeObject:
    def __init__(
        self,
        name,
    ):
        self.Name = name
        self.Label = name
        self.editor_modes = {}

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        setattr(
            self,
            property_name,
            None,
        )

    def setEditorMode(
        self,
        property_name,
        mode,
    ):
        self.editor_modes[
            property_name
        ] = mode


class FakeGroup:
    def __init__(
        self,
        name,
    ):
        self.Name = name
        self.Label = name
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
        self._counter = 0

    @property
    def Objects(
        self,
    ):
        return list(
            self.objects.values()
        )

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
        if (
            object_type
            in (
                "App::DocumentObjectGroup",
                "App::DocumentObjectGroupPython",
            )
        ):
            obj = FakeGroup(
                name
            )
        else:
            actual_name = name

            while actual_name in self.objects:
                self._counter += 1
                actual_name = (
                    f"{name}{self._counter:03d}"
                )

            obj = FakeObject(
                actual_name
            )

        self.objects[
            obj.Name
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


store = importlib.import_module(
    "forgecad.adapters.freecad.joint_constraint_store"
)

store.FreeCAD.Vector = FakeVector


def make_constraint():
    return CollinearThroughConstraint(
        axis_start=Point3D(
            -1000.0,
            25.0,
            10.0,
        ),
        axis_end=Point3D(
            1000.0,
            25.0,
            10.0,
        ),
    )


def test_save_creates_joint_constraints_group_and_record():
    document = FakeDocument()

    obj = store.save_joint_constraint(
        document,
        "0.000000,0.000000,0.000000",
        make_constraint(),
    )

    group = document.getObject(
        "ForgeCADJointConstraints"
    )

    assert group is not None
    assert obj in group.Group

    assert (
        obj.ConstraintKind
        == JointConstraintKind.COLLINEAR_THROUGH.value
    )

    assert obj.NodeKey == (
        "0.000000,0.000000,0.000000"
    )


def test_load_round_trips_collinear_constraint():
    document = FakeDocument()

    original = make_constraint()

    store.save_joint_constraint(
        document,
        "NKEY",
        original,
    )

    loaded = store.load_joint_constraint(
        document,
        "NKEY",
    )

    assert loaded == original


def test_save_updates_existing_record_instead_of_duplicating():
    document = FakeDocument()

    first = make_constraint()

    second = CollinearThroughConstraint(
        axis_start=Point3D(
            -500.0,
            0.0,
            0.0,
        ),
        axis_end=Point3D(
            1500.0,
            0.0,
            0.0,
        ),
    )

    first_obj = store.save_joint_constraint(
        document,
        "NKEY",
        first,
    )

    second_obj = store.save_joint_constraint(
        document,
        "NKEY",
        second,
    )

    assert second_obj is first_obj

    records = store.constraint_objects(
        document
    )

    assert records == (
        first_obj,
    )

    assert (
        store.load_joint_constraint(
            document,
            "NKEY",
        )
        == second
    )


def test_load_is_read_only_when_group_does_not_exist():
    document = FakeDocument()

    loaded = store.load_joint_constraint(
        document,
        "missing",
    )

    assert loaded is None

    assert (
        document.getObject(
            "ForgeCADJointConstraints"
        )
        is None
    )


def test_remove_deletes_constraint_record():
    document = FakeDocument()

    obj = store.save_joint_constraint(
        document,
        "NKEY",
        make_constraint(),
    )

    assert store.remove_joint_constraint(
        document,
        "NKEY",
    ) is True

    assert store.find_joint_constraint(
        document,
        "NKEY",
    ) is None

    assert document.getObject(
        obj.Name
    ) is None


def test_unknown_constraint_kind_loads_as_none():
    document = FakeDocument()

    obj = store.save_joint_constraint(
        document,
        "NKEY",
        make_constraint(),
    )

    obj.ConstraintKind = (
        "future_constraint"
    )

    assert store.load_joint_constraint(
        document,
        "NKEY",
    ) is None
