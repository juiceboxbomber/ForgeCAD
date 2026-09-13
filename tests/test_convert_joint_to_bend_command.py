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

def test_start_node_joint_is_supported_for_bent_tube_extension(monkeypatch):
    """A bent tube joined to a straight member at its StartNode should
    be recognized as a valid extension case.
    """

    bent_object = types.SimpleNamespace(
        Proxy=types.SimpleNamespace(
            replace_tube_definition=lambda *_args: None
        ),
        StartNode=types.SimpleNamespace(),
        EndNode=types.SimpleNamespace(),
    )

    straight_object = types.SimpleNamespace(
        MemberID="member-1",
        SourceLayoutID="layout-1",
    )

    assert (
        module.joint_conversion_mode(
            (
                bent_object,
                straight_object,
            )
        )
        == "extend"
    )


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



def test_prepend_existing_bent_object_keeps_identity_and_relinks_start(
    monkeypatch,
):
    """
    Extending a continuous bent tube from its StartNode must prepend the new
    design joint while preserving the existing bent-object identity and EndNode.
    """

    bent_object = FakeBentExtensionObject()

    old_start_node = object()
    old_end_node = bent_object.EndNode
    existing_design_joint = bent_object.DesignJointNode1
    new_start_node = object()

    bent_object.StartNode = old_start_node

    straight_object = FakeStraightExtensionObject(
        new_start_node
    )

    document = FakeExtensionDocument(
        (
            straight_object,
        )
    )

    replacement_tube = object()

    captured_joints = []

    def fake_design_joint_links(
        obj,
        joints,
    ):
        captured_joints[:] = list(
            joints
        )

        for index, joint in enumerate(
            joints,
            start=1,
        ):
            setattr(
                obj,
                f"DesignJointNode{index}",
                joint,
            )

        return obj

    monkeypatch.setattr(
        module,
        "ensure_bent_tube_design_joint_links",
        fake_design_joint_links,
        raising=False,
    )

    result = module.prepend_existing_bent_object(
        document=document,
        bent_object=bent_object,
        straight_object=straight_object,
        replacement_tube=replacement_tube,
        design_joint_node=old_start_node,
        new_start_node=new_start_node,
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
        bent_object.StartNode
        is new_start_node
    )

    assert (
        bent_object.EndNode
        is old_end_node
    )

    assert captured_joints == [
        old_start_node,
        existing_design_joint,
    ]

    assert (
        straight_object
        not in document.frame_group.Group
    )

    assert document.removed == [
        "ForgeCADMember003",
    ]



def test_prepend_existing_bend_preserves_layout_ownership_and_removes_only_member(
    monkeypatch,
):
    """
    StartNode extension must retain the consumed straight member's source layout
    as bend-owned design geometry while removing only the straight member object.
    """

    bent_object = FakeBentExtensionObject()

    old_start_node = object()
    old_end_node = bent_object.EndNode
    existing_design_joint = bent_object.DesignJointNode1
    new_start_node = object()

    bent_object.StartNode = old_start_node

    straight_object = FakeStraightExtensionObject(
        new_start_node
    )

    document = FakeExtensionDocument(
        (
            straight_object,
        )
    )

    replacement_tube = object()

    monkeypatch.setattr(
        module,
        "ensure_bent_tube_design_joint_links",
        lambda obj, joints: obj,
        raising=False,
    )

    monkeypatch.setattr(
        module,
        "ensure_bent_tube_node_links",
        lambda obj, start_node, end_node: (
            setattr(
                obj,
                "StartNode",
                start_node,
            )
            or setattr(
                obj,
                "EndNode",
                end_node,
            )
            or obj
        ),
        raising=False,
    )

    monkeypatch.setattr(
        module,
        "layout_object_for_id",
        lambda document, layout_id: layout_id,
        raising=False,
    )

    result = module.prepend_existing_bent_object(
        document=document,
        bent_object=bent_object,
        straight_object=straight_object,
        replacement_tube=replacement_tube,
        design_joint_node=old_start_node,
        new_start_node=new_start_node,
    )

    assert result is bent_object

    assert bent_object.SourceLayoutLines == [
        "L001",
        "L002",
        "L003",
    ]

    assert (
        bent_object.StartNode
        is new_start_node
    )

    assert (
        bent_object.EndNode
        is old_end_node
    )

    assert (
        straight_object
        not in document.frame_group.Group
    )

    assert document.removed == [
        "ForgeCADMember003",
    ]

    assert "L003" not in document.removed

    assert (
        existing_design_joint
        is bent_object.DesignJointNode1
    )

def test_start_node_extension_prepends_path_and_new_radius(
    monkeypatch,
):
    """
    Extending at the bent tube's StartNode must prepend the straight member,
    selected joint, and new bend radius ahead of the existing bent path.
    """

    joint_point = types.SimpleNamespace(
        x=0.0,
        y=0.0,
        z=0.0,
    )

    old_start_node = types.SimpleNamespace(
        Position=FakeVector(
            0.0,
            0.0,
            0.0,
        )
    )

    existing_design_joint = types.SimpleNamespace(
        Position=FakeVector(
            1000.0,
            0.0,
            0.0,
        )
    )

    old_end_node = types.SimpleNamespace(
        Position=FakeVector(
            2000.0,
            1000.0,
            0.0,
        )
    )

    new_start_node = types.SimpleNamespace(
        Position=FakeVector(
            -1000.0,
            0.0,
            0.0,
        )
    )

    current_tube = types.SimpleNamespace(
        bends=(
            types.SimpleNamespace(
                centerline_radius=125.0,
            ),
        ),
        profile=object(),
        material=object(),
    )

    class StartExtensionProxy:
        def replace_tube_definition(
            self,
            *_args,
        ):
            return None

        def _tube_from_properties(
            self,
            _obj,
        ):
            return current_tube

    bent_object = types.SimpleNamespace(
        Name="ForgeCADBentTube",
        Proxy=StartExtensionProxy(),
        StartNode=old_start_node,
        EndNode=old_end_node,
        DesignJointNode1=existing_design_joint,
    )

    straight_object = types.SimpleNamespace(
        Name="ForgeCADMember003",
        MemberID="M003",
        SourceLayoutID="L003",
        StartNode=old_start_node,
        EndNode=new_start_node,
    )

    joint = types.SimpleNamespace(
        is_simple=True,
        node=joint_point,
        members=(
            object(),
            object(),
        ),
    )

    joint_status = types.SimpleNamespace(
        joint=joint,
        node_key="J-START",
    )

    captured_build = {}
    captured_prepend = {}

    monkeypatch.setattr(
        module,
        "freecad_structural_objects_for_joint",
        lambda document, selected_joint: (
            bent_object,
            straight_object,
        ),
    )

    monkeypatch.setattr(
        module,
        "joint_node_object",
        lambda document, selected_joint_node: old_start_node,
    )

    monkeypatch.setattr(
        module,
        "design_joint_node_objects",
        lambda obj: (
            existing_design_joint,
        ),
    )

    monkeypatch.setattr(
        module,
        "fabrication_node_from_object",
        lambda node_object: node_object,
    )

    replacement_tube = object()

    def fake_build_multi_joint_bent_tube(
        *,
        nodes,
        centerline_radii_mm,
        profile,
        material,
    ):
        captured_build["nodes"] = nodes
        captured_build["radii"] = centerline_radii_mm
        captured_build["profile"] = profile
        captured_build["material"] = material
        return replacement_tube

    monkeypatch.setattr(
        module,
        "build_multi_joint_bent_tube",
        fake_build_multi_joint_bent_tube,
    )

    def fake_prepend_existing_bent_object(
        **kwargs,
    ):
        captured_prepend.update(
            kwargs
        )
        return bent_object

    monkeypatch.setattr(
        module,
        "prepend_existing_bent_object",
        fake_prepend_existing_bent_object,
    )

    monkeypatch.setattr(
        module,
        "extend_existing_bent_object",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError(
                "StartNode extension must not use the EndNode append helper."
            )
        ),
    )

    monkeypatch.setattr(
        module,
        "hide_design_geometry_for_bend",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        module,
        "refresh_joint_topology",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        module,
        "refresh_fabrication_for_document",
        lambda *args, **kwargs: None,
    )

    document = types.SimpleNamespace(
        recompute=lambda: None,
    )

    result = module.extend_bent_tube_from_joint(
        document,
        joint_status,
        75.0,
    )

    assert result is bent_object

    assert captured_build["nodes"] == (
        new_start_node,
        old_start_node,
        existing_design_joint,
        old_end_node,
    )

    assert captured_build["radii"] == (
        75.0,
        125.0,
    )

    assert (
        captured_prepend["bent_object"]
        is bent_object
    )

    assert (
        captured_prepend["straight_object"]
        is straight_object
    )

    assert (
        captured_prepend["replacement_tube"]
        is replacement_tube
    )

    assert (
        captured_prepend["design_joint_node"]
        is old_start_node
    )

    assert (
        captured_prepend["new_start_node"]
        is new_start_node
    )

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

