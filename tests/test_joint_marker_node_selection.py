"""Tests for node-first joint selection behavior."""

import importlib
import sys
import types


class FakeVector:
    """Minimal FreeCAD.Vector replacement."""

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


class FakeViewObject:
    """Minimal FreeCAD view object."""

    def __init__(
        self,
    ):
        self.Visibility = False
        self.Transparency = 0
        self.Selectable = True


class FakeObject:
    """Minimal FreeCAD document object."""

    def __init__(
        self,
    ):
        self.ViewObject = (
            FakeViewObject()
        )
        self.Shape = None
        self._editor_modes = {}

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        if (
            property_type
            == "App::PropertyVector"
        ):
            value = FakeVector()

        elif (
            property_type
            == "App::PropertyBool"
        ):
            value = False

        elif (
            property_type
            == "App::PropertyLength"
        ):
            value = 0.0

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
        self._editor_modes[
            property_name
        ] = mode


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecad.Vector = (
    FakeVector
)

fake_freecad.ActiveDocument = (
    None
)


fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)

fake_selection = types.SimpleNamespace(
    getSelection=lambda: [],
    clearSelection=lambda: None,
    addSelection=lambda obj: None,
)

fake_freecad_gui.Selection = (
    fake_selection
)

fake_freecad_gui.getMainWindow = (
    lambda: None
)

fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)


fake_part = types.ModuleType(
    "Part"
)

fake_part.makeSphere = (
    lambda radius, center: (
        "sphere",
        float(
            radius
        ),
        center,
    )
)


class FakeDialog:
    """Minimal Qt dialog base."""

    Accepted = 1


class FakeMessageBox:
    """Minimal QMessageBox replacement."""

    @staticmethod
    def warning(
        *args,
        **kwargs,
    ):
        return None


fake_qt_gui = types.SimpleNamespace(
    QDialog=FakeDialog,
    QMessageBox=FakeMessageBox,
    QLabel=type(
        "QLabel",
        (),
        {},
    ),
    QDoubleSpinBox=type(
        "QDoubleSpinBox",
        (),
        {},
    ),
    QFormLayout=type(
        "QFormLayout",
        (),
        {},
    ),
    QDialogButtonBox=type(
        "QDialogButtonBox",
        (),
        {
            "Ok": 1,
            "Cancel": 2,
        },
    ),
    QVBoxLayout=type(
        "QVBoxLayout",
        (),
        {},
    ),
)


fake_pyside = types.ModuleType(
    "PySide"
)

fake_pyside.QtGui = (
    fake_qt_gui
)


sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = fake_freecad_gui

sys.modules[
    "Part"
] = fake_part

sys.modules[
    "PySide"
] = fake_pyside


joint_objects = importlib.import_module(
    "forgecad.adapters.freecad.joint_status_objects"
)

convert_command = importlib.import_module(
    "forgecad.adapters.freecad.commands.convert_joint_to_bend"
)


def test_joint_marker_is_nonselectable_in_3d_view(
    monkeypatch,
):
    """Joint display spheres must not block selection of real nodes."""

    obj = FakeObject()

    obj.VisualCategory = (
        "automatic"
    )

    obj.Position = FakeVector(
        100.0,
        200.0,
        300.0,
    )

    joint_objects.configure_joint_marker(
        obj
    )

    assert (
        obj.ViewObject.Visibility
        is True
    )

    assert (
        obj.ViewObject.Selectable
        is False
    )


def test_forgecad_node_is_valid_joint_selection():
    """A persistent ForgeCAD node can be used to select a joint."""

    node = types.SimpleNamespace(
        NodeID="N001",
        Position=FakeVector(
            1000.0,
            0.0,
            0.0,
        ),
    )

    assert (
        convert_command
        .is_joint_node_selection(
            node
        )
        is True
    )


def test_unrelated_object_is_not_joint_node_selection():
    """Objects without ForgeCAD node metadata are rejected."""

    obj = types.SimpleNamespace(
        Position=FakeVector(
            0.0,
            0.0,
            0.0,
        )
    )

    assert (
        convert_command
        .is_joint_node_selection(
            obj
        )
        is False
    )


def test_joint_status_can_be_resolved_from_node(
    monkeypatch,
):
    """Node selection resolves to the same current joint review item."""

    node = types.SimpleNamespace(
        NodeID="N001",
        Position=FakeVector(
            1000.0,
            0.0,
            0.0,
        ),
    )

    matching_joint = types.SimpleNamespace(
        node=types.SimpleNamespace(
            x=1000.0,
            y=0.0,
            z=0.0,
        )
    )

    expected = types.SimpleNamespace(
        node_key="1000,0,0",
        joint=matching_joint,
    )

    review = types.SimpleNamespace(
        joints=(
            expected,
        )
    )

    monkeypatch.setattr(
        convert_command,
        "joint_review_for_document",
        lambda document: review,
    )

    result = (
        convert_command
        .joint_status_for_node(
            object(),
            node,
        )
    )

    assert result is expected


def test_node_without_current_joint_is_rejected(
    monkeypatch,
):
    """A normal node with no current joint cannot be converted."""

    node = types.SimpleNamespace(
        NodeID="N001",
        Position=FakeVector(
            1000.0,
            0.0,
            0.0,
        ),
    )

    review = types.SimpleNamespace(
        joints=()
    )

    monkeypatch.setattr(
        convert_command,
        "joint_review_for_document",
        lambda document: review,
    )

    try:
        convert_command.joint_status_for_node(
            object(),
            node,
        )

    except ValueError as error:
        assert (
            "joint"
            in str(
                error
            ).lower()
        )

    else:
        raise AssertionError(
            "Expected ValueError for a node without a joint."
        )
    