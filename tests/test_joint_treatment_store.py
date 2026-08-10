"""Tests for persistent ForgeCAD joint-treatment storage."""

import sys
import types


class FakeVector:
    """Minimal FreeCAD Vector replacement."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


# ---------------------------------------------------------
# Minimal FreeCAD test stubs
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.Vector = (
    FakeVector
)

fake_freecadgui = types.ModuleType(
    "FreeCADGui"
)

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = fake_freecadgui

sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad.joint_treatment_store import (
    coordinate_key,
    decode_layout_ids,
    encode_layout_ids,
    find_joint_treatment,
    load_joint_treatment,
    node_key,
    normalize_layout_ids,
    remove_joint_treatment,
    save_joint_treatment,
    vector_key,
)


class FakeNode:
    """Minimal domain-node replacement."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


class FakeObject:
    """Minimal FreeCAD document object."""

    _next_number = 1

    def __init__(
        self,
        type_name,
        name,
    ):
        self.TypeId = (
            type_name
        )

        self.Name = (
            f"{name}"
            f"{FakeObject._next_number}"
        )

        FakeObject._next_number += 1

        self.Label = (
            self.Name
        )

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
        return None


class FakeGroup(
    FakeObject
):
    """Minimal FreeCAD document group."""

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
    """Minimal FreeCAD document replacement."""

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
        type_name,
        name,
    ):
        if (
            "Group"
            in type_name
        ):
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

        # Mirror FreeCAD's normal behavior where the requested
        # internal name can be found directly when available.
        if name not in self.objects:
            self.objects[
                name
            ] = obj

        return obj

    def removeObject(
        self,
        name,
    ):
        obj = self.objects.get(
            name
        )

        if obj is None:
            return

        keys_to_remove = [
            key
            for key, value
            in self.objects.items()
            if value is obj
        ]

        for key in keys_to_remove:
            del self.objects[
                key
            ]

    def recompute(
        self,
    ):
        self.recompute_count += 1


def test_coordinate_key_is_stable():
    assert coordinate_key(
        1,
        2.5,
        -3,
    ) == (
        "1.000000,"
        "2.500000,"
        "-3.000000"
    )


def test_node_key_uses_node_coordinates():
    node = FakeNode(
        10,
        20,
        30,
    )

    assert node_key(
        node
    ) == (
        "10.000000,"
        "20.000000,"
        "30.000000"
    )


def test_vector_key_matches_node_key_format():
    vector = FakeVector(
        10,
        20,
        30,
    )

    assert vector_key(
        vector
    ) == (
        "10.000000,"
        "20.000000,"
        "30.000000"
    )


def test_layout_ids_are_normalized():
    assert normalize_layout_ids(
        (
            " L001 ",
            "",
            "L002",
            "L001",
        )
    ) == (
        "L001",
        "L002",
    )


def test_layout_ids_round_trip():
    encoded = encode_layout_ids(
        (
            "L001",
            "L002",
        )
    )

    assert encoded == (
        "L001|L002"
    )

    assert decode_layout_ids(
        encoded
    ) == (
        "L001",
        "L002",
    )


def test_save_creates_treatment_record():
    document = (
        FakeDocument()
    )

    obj = save_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
        "member_through",
        (
            "L001",
        ),
    )

    assert obj.NodeKey == (
        "0.000000,0.000000,0.000000"
    )

    assert obj.TreatmentMode == (
        "member_through"
    )

    assert obj.ThroughLayoutIDs == (
        "L001"
    )


def test_saved_object_is_in_joint_treatments_group():
    document = (
        FakeDocument()
    )

    obj = save_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
        "both_coped",
    )

    group = document.getObject(
        "ForgeCADJointTreatments"
    )

    assert obj in group.Group


def test_save_updates_existing_record():
    document = (
        FakeDocument()
    )

    first = save_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
        "member_through",
        (
            "L001",
        ),
    )

    second = save_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
        "both_coped",
    )

    assert second is first

    assert second.TreatmentMode == (
        "both_coped"
    )

    assert second.ThroughLayoutIDs == (
        ""
    )


def test_different_nodes_create_different_records():
    document = (
        FakeDocument()
    )

    first = save_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
        "member_through",
        (
            "L001",
        ),
    )

    second = save_joint_treatment(
        document,
        "500.000000,0.000000,0.000000",
        "member_through",
        (
            "L002",
        ),
    )

    assert (
        first
        is not second
    )


def test_find_returns_saved_treatment():
    document = (
        FakeDocument()
    )

    saved = save_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
        "both_coped",
    )

    found = find_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
    )

    assert (
        found
        is saved
    )


def test_load_returns_mode_and_layout_ids():
    document = (
        FakeDocument()
    )

    save_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
        "through_pair",
        (
            "L001",
            "L002",
        ),
    )

    loaded = load_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
    )

    assert loaded == (
        "through_pair",
        (
            "L001",
            "L002",
        ),
    )


def test_load_returns_none_when_missing():
    document = (
        FakeDocument()
    )

    assert load_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
    ) is None


def test_remove_deletes_treatment():
    document = (
        FakeDocument()
    )

    save_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
        "both_coped",
    )

    assert remove_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
    )

    assert load_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
    ) is None


def test_remove_missing_treatment_returns_false():
    document = (
        FakeDocument()
    )

    assert not remove_joint_treatment(
        document,
        "0.000000,0.000000,0.000000",
    )
    