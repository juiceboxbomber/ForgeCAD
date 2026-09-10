"""Tests for additive explicit cope persistence."""

import sys
import types

sys.modules["FreeCAD"] = types.ModuleType("FreeCAD")
sys.modules["Part"] = types.ModuleType("Part")
sys.modules["FreeCADGui"] = types.ModuleType("FreeCADGui")

from forgecad.adapters.freecad.joint_treatment_store import (
    load_joint_cope_pairs,
    save_joint_cope_pair,
    save_joint_treatment,
)


class FakeTreatmentObject:
    def __init__(self):
        self.Name = "ForgeCADJointTreatment"
        self.NodeKey = "0.000000,0.000000,0.000000"
        self.TreatmentMode = "both_coped"
        self.ThroughLayoutIDs = "L001|L002"

    def addProperty(
        self,
        type_name,
        name,
        group,
    ):
        setattr(
            self,
            name,
            "",
        )

    def setEditorMode(
        self,
        name,
        mode,
    ):
        pass


class FakeGroup:
    def __init__(
        self,
        obj,
    ):
        self.Group = [
            obj
        ]


class FakeDocument:
    def __init__(
        self,
        obj,
    ):
        self.obj = obj
        self.group = FakeGroup(
            obj
        )

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADJointTreatments":
            return self.group

        if name == "ForgeCADProject":
            return None

        return None

    def recompute(
        self,
    ):
        pass


def test_explicit_cope_is_additive_to_saved_miter():
    obj = FakeTreatmentObject()
    document = FakeDocument(
        obj
    )

    save_joint_cope_pair(
        document,
        obj.NodeKey,
        "L003",
        "L001",
    )

    assert load_joint_cope_pairs(
        document,
        obj.NodeKey,
    ) == (
        (
            "L003",
            "L001",
        ),
    )

    assert obj.TreatmentMode == "both_coped"
    assert obj.ThroughLayoutIDs == "L001|L002"


def test_resaving_primary_treatment_preserves_explicit_copes():
    obj = FakeTreatmentObject()
    document = FakeDocument(
        obj
    )

    save_joint_cope_pair(
        document,
        obj.NodeKey,
        "L003",
        "L001",
    )

    save_joint_treatment(
        document,
        obj.NodeKey,
        "both_coped",
        (
            "L001",
            "L002",
        ),
    )

    assert load_joint_cope_pairs(
        document,
        obj.NodeKey,
    ) == (
        (
            "L003",
            "L001",
        ),
    )
