"""Tests for enum persistence in the joint-treatment store."""

import sys
import types


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.Vector = (
    FakeVector
)

sys.modules[
    "FreeCAD"
] = fake_freecad

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


from forgecad.fabrication.joint_treatment import (
    JointTreatmentMode,
)
from forgecad.adapters.freecad.joint_treatment_store import (
    load_joint_treatment,
    save_joint_treatment,
)


class FakeObject:
    _next_number = 1

    def __init__(
        self,
        type_name,
        name,
    ):
        self.Name = (
            f"{name}"
            f"{FakeObject._next_number}"
        )

        FakeObject._next_number += 1

        self.Label = self.Name

    def addProperty(
        self,
        property_type,
        property_name,
        property_group,
    ):
        setattr(
            self,
            property_name,
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
        type_name,
        name,
    ):
        super().__init__(
            type_name,
            name,
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

    def getObject(
        self,
        name,
    ):
        return self.objects.get(
            name
        )

    def addObject(
        self,
        type_name,
        name,
    ):
        if "Group" in type_name:
            obj = FakeGroup(
                type_name,
                name,
            )
        else:
            obj = FakeObject(
                type_name,
                name,
            )

        self.objects[
            obj.Name
        ] = obj

        if name not in self.objects:
            self.objects[
                name
            ] = obj

        return obj

    def removeObject(
        self,
        name,
    ):
        pass

    def recompute(
        self,
    ):
        pass


def test_enum_mode_is_saved_using_enum_value():
    document = FakeDocument()

    save_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
        JointTreatmentMode.MEMBER_THROUGH,
        (
            "L001",
        ),
    )

    loaded = load_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
    )

    assert loaded == (
        "member_through",
        (
            "L001",
        ),
    )
    