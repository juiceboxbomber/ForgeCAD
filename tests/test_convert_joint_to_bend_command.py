"""Tests for the FreeCAD Convert Joint to Bend command helpers."""

import importlib
import sys
import types


class FakeVector:
    def __init__(
        self,
        x=0.0,
        y=0.0,
        z=0.0,
    ):
        self.x = float(
            x
        )
        self.y = float(
            y
        )
        self.z = float(
            z
        )


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.Vector = FakeVector
fake_freecad.ActiveDocument = None

sys.modules[
    "FreeCAD"
] = fake_freecad


fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_freecad_gui.Selection = types.SimpleNamespace(
    getSelection=lambda: [],
)

fake_freecad_gui.addCommand = (
    lambda *args,
    **kwargs: None
)

sys.modules[
    "FreeCADGui"
] = fake_freecad_gui


class FakeDialog:
    Accepted = 1


class FakeWidget:
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        pass


fake_qt_gui = types.SimpleNamespace(
    QDialog=FakeWidget,
    QLabel=FakeWidget,
    QDoubleSpinBox=FakeWidget,
    QFormLayout=FakeWidget,
    QDialogButtonBox=FakeDialog,
    QVBoxLayout=FakeWidget,
    QMessageBox=FakeWidget,
)

fake_pyside = types.ModuleType(
    "PySide"
)

fake_pyside.QtGui = fake_qt_gui

sys.modules[
    "PySide"
] = fake_pyside


module = importlib.import_module(
    "forgecad.adapters.freecad.commands.convert_joint_to_bend"
)


class FakeDocument:
    def __init__(
        self,
    ):
        self.events = []

    def openTransaction(
        self,
        label,
    ):
        self.events.append(
            (
                "open",
                label,
            )
        )

    def commitTransaction(
        self,
    ):
        self.events.append(
            (
                "commit",
                None,
            )
        )

    def abortTransaction(
        self,
    ):
        self.events.append(
            (
                "abort",
                None,
            )
        )


class FakeMarker:
    JointID = "J001"
    NodeKey = "0.000000,0.000000,0.000000"
    Position = FakeVector(
        0.0,
        0.0,
        0.0,
    )


def test_joint_marker_detection_requires_marker_properties():
    assert module.is_joint_marker(
        FakeMarker()
    )

    assert not module.is_joint_marker(
        object()
    )


def test_convert_transaction_helpers_use_one_stable_transaction():
    document = FakeDocument()

    started = (
        module.begin_convert_joint_to_bend_transaction(
            document
        )
    )

    assert started is True

    module.finish_convert_joint_to_bend_transaction(
        document,
        started,
    )

    assert document.events == [
        (
            "open",
            "Convert ForgeCAD Joint to Bend",
        ),
        (
            "commit",
            None,
        ),
    ]


def test_convert_transaction_can_abort():
    document = FakeDocument()

    started = (
        module.begin_convert_joint_to_bend_transaction(
            document
        )
    )

    module.abort_convert_joint_to_bend_transaction(
        document,
        started,
    )

    assert document.events == [
        (
            "open",
            "Convert ForgeCAD Joint to Bend",
        ),
        (
            "abort",
            None,
        ),
    ]


def test_joint_status_resolution_uses_marker_node_key():
    marker = FakeMarker()

    expected = object()

    original_review = (
        module.joint_review_for_document
    )

    module.joint_review_for_document = (
        lambda document: types.SimpleNamespace(
            joints=(
                types.SimpleNamespace(
                    node_key="elsewhere",
                ),
                types.SimpleNamespace(
                    node_key=marker.NodeKey,
                    payload=expected,
                ),
            )
        )
    )

    try:
        result = module.joint_status_for_marker(
            object(),
            marker,
        )

    finally:
        module.joint_review_for_document = (
            original_review
        )

    assert result.payload is expected


def test_mixed_bent_and_straight_joint_maps_to_exact_freecad_objects(
    monkeypatch,
):
    bent_domain_member = (
        object()
    )

    straight_domain_member = (
        object()
    )

    joint = types.SimpleNamespace(
        is_simple=True,
        members=(
            bent_domain_member,
            straight_domain_member,
        ),
    )

    bent_object = types.SimpleNamespace(
        Name="ForgeCADBentTube"
    )

    straight_object = types.SimpleNamespace(
        Name="ForgeCADMember"
    )

    document = (
        object()
    )

    monkeypatch.setattr(
        module,
        "frame_member_objects",
        lambda document: [
            bent_object,
            straight_object,
        ],
    )

    domain_by_object = {
        id(
            bent_object
        ): bent_domain_member,
        id(
            straight_object
        ): straight_domain_member,
    }

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: domain_by_object[
            id(
                obj
            )
        ],
    )

    result = (
        module.freecad_structural_objects_for_joint(
            document,
            joint,
        )
    )

    assert result == (
        bent_object,
        straight_object,
    )


def test_mixed_joint_mapping_preserves_domain_member_order(
    monkeypatch,
):
    straight_domain_member = (
        object()
    )

    bent_domain_member = (
        object()
    )

    joint = types.SimpleNamespace(
        is_simple=True,
        members=(
            straight_domain_member,
            bent_domain_member,
        ),
    )

    bent_object = types.SimpleNamespace(
        Name="ForgeCADBentTube"
    )

    straight_object = types.SimpleNamespace(
        Name="ForgeCADMember"
    )

    monkeypatch.setattr(
        module,
        "frame_member_objects",
        lambda document: [
            bent_object,
            straight_object,
        ],
    )

    domain_by_object = {
        id(
            bent_object
        ): bent_domain_member,
        id(
            straight_object
        ): straight_domain_member,
    }

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: domain_by_object[
            id(
                obj
            )
        ],
    )

    result = (
        module.freecad_structural_objects_for_joint(
            object(),
            joint,
        )
    )

    assert result == (
        straight_object,
        bent_object,
    )


class FakeGroup:
    def __init__(
        self,
        objects=(),
    ):
        self.Group = list(
            objects
        )

    def removeObject(
        self,
        obj,
    ):
        if obj in self.Group:
            self.Group.remove(
                obj
            )


class FakeExtensionDocument:
    def __init__(
        self,
        frame_objects=(),
    ):
        self.frame_group = FakeGroup(
            frame_objects
        )

        self.removed = []
        self.recompute_count = 0

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADFrame":
            return self.frame_group

        return None

    def removeObject(
        self,
        name,
    ):
        self.removed.append(
            name
        )

    def recompute(
        self,
    ):
        self.recompute_count += 1


class FakeExtensionProxy:
    def __init__(
        self,
    ):
        self.replacements = []

    def replace_tube_definition(
        self,
        obj,
        tube,
    ):
        self.replacements.append(
            (
                obj,
                tube,
            )
        )


class FakeBentExtensionObject:
    def __init__(
        self,
    ):
        self.Name = "ForgeCADBentTube"
        self.Proxy = FakeExtensionProxy()

        self.EndNode = (
            object()
        )

        self.DesignJointNode = (
            object()
        )

        self.DesignJointNode1 = (
            self.DesignJointNode
        )

        self.SourceLayoutLines = [
            "L001",
            "L002",
        ]


class FakeStraightExtensionObject:
    def __init__(
        self,
        outer_node,
    ):
        self.Name = "ForgeCADMember003"
        self.MemberID = "M003"
        self.SourceLayoutID = "L003"
        self.EndNode = outer_node


def test_extend_existing_bent_object_mutates_same_object_in_place(
    monkeypatch,
):
    bent_object = (
        FakeBentExtensionObject()
    )

    new_end_node = (
        object()
    )

    straight_object = (
        FakeStraightExtensionObject(
            new_end_node
        )
    )

    document = FakeExtensionDocument(
        (
            straight_object,
        )
    )

    second_design_joint = (
        object()
    )

    replacement_tube = (
        object()
    )

    monkeypatch.setattr(
        module,
        "ensure_bent_tube_design_joint_links",
        lambda obj, joints: (
            setattr(
                obj,
                "DesignJointNode2",
                joints[
                    1
                ],
            )
            or obj
        ),
        raising=False,
    )

    result = (
        module.extend_existing_bent_object(
            document=document,
            bent_object=bent_object,
            straight_object=straight_object,
            replacement_tube=replacement_tube,
            design_joint_node=second_design_joint,
            new_end_node=new_end_node,
        )
    )

    assert result is bent_object

    assert (
        bent_object.Proxy.replacements
        == [
            (
                bent_object,
                replacement_tube,
            )
        ]
    )

    assert (
        bent_object.EndNode
        is new_end_node
    )

    assert (
        bent_object.DesignJointNode2
        is second_design_joint
    )

    assert (
        "ForgeCADMember003"
        in document.removed
    )


def test_extend_existing_bend_preserves_and_extends_layout_ownership(
    monkeypatch,
):
    bent_object = (
        FakeBentExtensionObject()
    )

    new_end_node = (
        object()
    )

    straight_object = (
        FakeStraightExtensionObject(
            new_end_node
        )
    )

    document = FakeExtensionDocument(
        (
            straight_object,
        )
    )

    monkeypatch.setattr(
        module,
        "ensure_bent_tube_design_joint_links",
        lambda obj, joints: obj,
        raising=False,
    )

    module.extend_existing_bent_object(
        document=document,
        bent_object=bent_object,
        straight_object=straight_object,
        replacement_tube=object(),
        design_joint_node=object(),
        new_end_node=new_end_node,
    )

    assert bent_object.SourceLayoutLines == [
        "L001",
        "L002",
        "L003",
    ]


def test_extend_existing_bend_removes_straight_without_deleting_layout(
    monkeypatch,
):
    bent_object = (
        FakeBentExtensionObject()
    )

    new_end_node = (
        object()
    )

    straight_object = (
        FakeStraightExtensionObject(
            new_end_node
        )
    )

    document = FakeExtensionDocument(
        (
            straight_object,
        )
    )

    monkeypatch.setattr(
        module,
        "ensure_bent_tube_design_joint_links",
        lambda obj, joints: obj,
        raising=False,
    )

    module.extend_existing_bent_object(
        document=document,
        bent_object=bent_object,
        straight_object=straight_object,
        replacement_tube=object(),
        design_joint_node=object(),
        new_end_node=new_end_node,
    )

    assert (
        straight_object
        not in document.frame_group.Group
    )

    assert document.removed == [
        "ForgeCADMember003",
    ]


def test_conversion_path_detects_existing_bent_plus_straight():
    """
    A mixed joint must use the extension path rather than the original
    two-straight-member conversion path.
    """

    bent = types.SimpleNamespace(
        Name="ForgeCADBentTube",
        Proxy=types.SimpleNamespace(
            replace_tube_definition=lambda *args: None,
        ),
    )

    straight = types.SimpleNamespace(
        Name="ForgeCADMember",
        MemberID="M003",
        SourceLayoutID="L003",
    )

    assert (
        module.joint_conversion_mode(
            (
                bent,
                straight,
            )
        )
        == "extend"
    )


def test_conversion_path_detects_two_straight_members():
    """
    The original first-corner conversion remains unchanged.
    """

    first = types.SimpleNamespace(
        Name="ForgeCADMember001",
        MemberID="M001",
        SourceLayoutID="L001",
    )

    second = types.SimpleNamespace(
        Name="ForgeCADMember002",
        MemberID="M002",
        SourceLayoutID="L002",
    )

    assert (
        module.joint_conversion_mode(
            (
                first,
                second,
            )
        )
        == "create"
    )

