"""Tests for ForgeCAD FreeCAD joint-status objects."""

import sys
import types


class FakeVector:
    """Minimal FreeCAD vector."""

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


from forgecad.adapters.freecad import (
    joint_status_objects,
)


# The adapter may already have been imported by another test
# using a different FreeCAD stub. Patch the module reference
# directly so this test is independent of collection order.
joint_status_objects.FreeCAD = (
    fake_freecad
)


joint_status_objects.FreeCADGui = (
    sys.modules[
        "FreeCADGui"
    ]
)

joint_status_objects.Part = (
    sys.modules[
        "Part"
    ]
)


from forgecad.services.joint_status import (
    joint_status_from_saved_treatment,
)


class FakeObject:
    """Minimal FreeCAD object."""

    _number = 1

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
            f"{FakeObject._number}"
        )

        FakeObject._number += 1

        self.Label = self.Name

    def addProperty(
        self,
        property_type,
        property_name,
        property_group,
    ):
        if (
            property_type
            == "App::PropertyBool"
        ):
            value = False

        elif (
            property_type
            == "App::PropertyVector"
        ):
            value = FakeVector(
                0,
                0,
                0,
            )

        else:
            value = ""

        setattr(
            self,
            property_name,
            value,
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
    """Minimal FreeCAD group."""

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
    """Minimal FreeCAD document."""

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

        keys = [
            key
            for key, value
            in self.objects.items()
            if value is obj
        ]

        for key in keys:
            del self.objects[
                key
            ]

    def recompute(
        self,
    ):
        pass


class FakeNode:
    """Minimal domain node."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


class FakeJoint:
    """Minimal domain joint."""

    def __init__(
        self,
        node,
    ):
        self.node = node


class FakeDocumentJointStatus:
    """Minimal adapter status item."""

    def __init__(
        self,
        node_key,
        saved_treatment,
        node=None,
    ):
        self.node_key = node_key

        self.status = (
            joint_status_from_saved_treatment(
                saved_treatment
            )
        )

        self.joint = FakeJoint(
            node
            or FakeNode(
                0,
                0,
                0,
            )
        )


class FakeSummary:
    pass


class FakeReview:
    def __init__(
        self,
        joints,
    ):
        self.joints = tuple(
            joints
        )

        self.summary = (
            FakeSummary()
        )


def test_create_joint_status_object_sets_identity():
    document = (
        FakeDocument()
    )

    item = (
        FakeDocumentJointStatus(
            "0.000000,0.000000,0.000000",
            None,
        )
    )

    obj = (
        joint_status_objects
        .create_joint_status_object(
            document,
            "J001",
            item,
        )
    )

    assert obj.JointID == (
        "J001"
    )

    assert obj.NodeKey == (
        "0.000000,0.000000,0.000000"
    )


def test_unreviewed_label():
    document = (
        FakeDocument()
    )

    item = (
        FakeDocumentJointStatus(
            "0.000000,0.000000,0.000000",
            None,
        )
    )

    obj = (
        joint_status_objects
        .create_joint_status_object(
            document,
            "J001",
            item,
        )
    )

    assert obj.Label == (
        "[ ] J001 - Unreviewed"
    )

    assert not obj.Reviewed


def test_mitered_label():
    document = (
        FakeDocument()
    )

    item = (
        FakeDocumentJointStatus(
            "0.000000,0.000000,0.000000",
            (
                "both_coped",
                (),
            ),
        )
    )

    obj = (
        joint_status_objects
        .create_joint_status_object(
            document,
            "J001",
            item,
        )
    )

    assert obj.Label == (
        "[M] J001 - Both Mitered"
    )

    assert obj.Reviewed
    assert obj.ManualTreatment


def test_position_is_stored():
    document = (
        FakeDocument()
    )

    item = (
        FakeDocumentJointStatus(
            "10.000000,20.000000,30.000000",
            None,
            node=FakeNode(
                10,
                20,
                30,
            ),
        )
    )

    obj = (
        joint_status_objects
        .create_joint_status_object(
            document,
            "J001",
            item,
        )
    )

    assert obj.Position.x == 10
    assert obj.Position.y == 20
    assert obj.Position.z == 30


def test_rebuild_places_objects_in_joints_group(
    monkeypatch,
):
    document = (
        FakeDocument()
    )

    review = FakeReview(
        [
            FakeDocumentJointStatus(
                "0.000000,0.000000,0.000000",
                None,
            ),
            FakeDocumentJointStatus(
                "500.000000,0.000000,0.000000",
                (
                    "auto",
                    (),
                ),
                node=FakeNode(
                    500,
                    0,
                    0,
                ),
            ),
        ]
    )

    monkeypatch.setattr(
        joint_status_objects,
        "joint_review_for_document",
        lambda document: review,
    )

    created = (
        joint_status_objects
        .rebuild_joint_status_objects(
            document
        )
    )

    group = document.getObject(
        "ForgeCADJoints"
    )

    assert len(
        created
    ) == 2

    assert list(
        created
    ) == group.Group


def test_rebuild_assigns_sequential_joint_ids(
    monkeypatch,
):
    document = (
        FakeDocument()
    )

    review = FakeReview(
        [
            FakeDocumentJointStatus(
                "0.000000,0.000000,0.000000",
                None,
            ),
            FakeDocumentJointStatus(
                "500.000000,0.000000,0.000000",
                None,
                node=FakeNode(
                    500,
                    0,
                    0,
                ),
            ),
        ]
    )

    monkeypatch.setattr(
        joint_status_objects,
        "joint_review_for_document",
        lambda document: review,
    )

    created = (
        joint_status_objects
        .rebuild_joint_status_objects(
            document
        )
    )

    assert (
        created[
            0
        ].JointID
        == "J001"
    )

    assert (
        created[
            1
        ].JointID
        == "J002"
    )


def test_rebuild_clears_old_joint_objects(
    monkeypatch,
):
    document = (
        FakeDocument()
    )

    groups = (
        joint_status_objects
        .initialize_project_tree(
            document
        )
    )

    old = document.addObject(
        "App::FeaturePython",
        "ForgeCADJoint",
    )

    groups[
        "Joints"
    ].addObject(
        old
    )

    monkeypatch.setattr(
        joint_status_objects,
        "joint_review_for_document",
        lambda document: FakeReview(
            []
        ),
    )

    created = (
        joint_status_objects
        .rebuild_joint_status_objects(
            document
        )
    )

    assert created == ()

    assert (
        groups[
            "Joints"
        ].Group
        == []
    )


def test_none_document_returns_empty():
    assert (
        joint_status_objects
        .rebuild_joint_status_objects(
            None
        )
        == ()
    )
    