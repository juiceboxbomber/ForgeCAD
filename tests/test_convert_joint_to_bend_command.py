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
