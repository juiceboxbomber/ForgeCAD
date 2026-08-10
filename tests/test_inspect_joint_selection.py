"""Tests for ForgeCAD Inspect Joint selection resolution."""

import sys
import types


# ---------------------------------------------------------
# Stub FreeCAD modules BEFORE importing ForgeCAD adapters.
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
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


# ---------------------------------------------------------
# Minimal PySide stub.
# ---------------------------------------------------------

fake_pyside = types.ModuleType(
    "PySide"
)

fake_qtgui = types.ModuleType(
    "QtGui"
)


class FakeQDialog:
    pass


fake_qtgui.QDialog = (
    FakeQDialog
)

fake_pyside.QtGui = (
    fake_qtgui
)

sys.modules[
    "PySide"
] = fake_pyside

sys.modules[
    "PySide.QtGui"
] = fake_qtgui


from forgecad.adapters.freecad.commands import (
    inspect_joint,
)


class FakeVector:
    """Minimal FreeCAD-like vector."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = x
        self.y = y
        self.z = z


class FakeNodeObject:
    """Minimal ForgeCAD node object."""

    def __init__(
        self,
        node_id,
        position,
    ):
        self.NodeID = (
            node_id
        )

        self.Position = (
            position
        )


class FakeJointStatusObject:
    """Minimal Joints-tree status object."""

    def __init__(
        self,
        joint_id,
        node_key,
        position,
    ):
        self.JointID = (
            joint_id
        )

        self.NodeKey = (
            node_key
        )

        self.Position = (
            position
        )

        self.ReviewStatus = (
            "unreviewed"
        )


class FakeGroup:
    """Minimal FreeCAD group."""

    def __init__(
        self,
        objects=None,
    ):
        self.Group = list(
            objects
            or []
        )


class FakeDocument:
    """Minimal FreeCAD document."""

    def __init__(
        self,
        nodes=None,
    ):
        self.nodes_group = (
            FakeGroup(
                nodes
                or []
            )
        )

    def getObject(
        self,
        name,
    ):
        if name == (
            "ForgeCADNodes"
        ):
            return (
                self.nodes_group
            )

        return None


def test_node_selection_returns_same_node():
    node = FakeNodeObject(
        "N001",
        FakeVector(
            0,
            0,
            0,
        ),
    )

    document = FakeDocument(
        [
            node,
        ]
    )

    resolved = (
        inspect_joint
        .node_object_for_inspection(
            document,
            node,
        )
    )

    assert resolved is node


def test_joint_status_object_is_recognized():
    obj = FakeJointStatusObject(
        "J001",
        "0.000000,0.000000,0.000000",
        FakeVector(
            0,
            0,
            0,
        ),
    )

    assert (
        inspect_joint
        .is_joint_status_object(
            obj
        )
    )


def test_normal_node_is_not_joint_status_object():
    obj = FakeNodeObject(
        "N001",
        FakeVector(
            0,
            0,
            0,
        ),
    )

    assert not (
        inspect_joint
        .is_joint_status_object(
            obj
        )
    )


def test_joint_status_selection_resolves_node():
    node = FakeNodeObject(
        "N007",
        FakeVector(
            500,
            250,
            100,
        ),
    )

    joint_status = (
        FakeJointStatusObject(
            "J003",
            (
                "500.000000,"
                "250.000000,"
                "100.000000"
            ),
            FakeVector(
                500,
                250,
                100,
            ),
        )
    )

    document = FakeDocument(
        [
            node,
        ]
    )

    resolved = (
        inspect_joint
        .node_object_for_inspection(
            document,
            joint_status,
        )
    )

    assert resolved is node


def test_position_matching_uses_existing_precision():
    node = FakeNodeObject(
        "N007",
        FakeVector(
            500.0000001,
            250,
            100,
        ),
    )

    joint_status = (
        FakeJointStatusObject(
            "J003",
            (
                "500.000000,"
                "250.000000,"
                "100.000000"
            ),
            FakeVector(
                500.0000002,
                250,
                100,
            ),
        )
    )

    document = FakeDocument(
        [
            node,
        ]
    )

    resolved = (
        inspect_joint
        .node_object_for_inspection(
            document,
            joint_status,
        )
    )

    assert resolved is node


def test_joint_status_returns_none_when_node_missing():
    joint_status = (
        FakeJointStatusObject(
            "J003",
            (
                "500.000000,"
                "250.000000,"
                "100.000000"
            ),
            FakeVector(
                500,
                250,
                100,
            ),
        )
    )

    document = FakeDocument(
        []
    )

    resolved = (
        inspect_joint
        .node_object_for_inspection(
            document,
            joint_status,
        )
    )

    assert resolved is None


def test_invalid_selection_returns_none():
    document = FakeDocument()

    resolved = (
        inspect_joint
        .node_object_for_inspection(
            document,
            object(),
        )
    )

    assert resolved is None


def test_missing_nodes_group_returns_none():
    class DocumentWithoutNodes:
        def getObject(
            self,
            name,
        ):
            return None

    joint_status = (
        FakeJointStatusObject(
            "J001",
            "0.000000,0.000000,0.000000",
            FakeVector(
                0,
                0,
                0,
            ),
        )
    )

    resolved = (
        inspect_joint
        .node_object_for_inspection(
            DocumentWithoutNodes(),
            joint_status,
        )
    )

    assert resolved is None
    