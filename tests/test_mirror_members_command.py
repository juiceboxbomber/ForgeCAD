"""Tests for interactive centerline-based Mirror Members."""

import sys
import types
from types import SimpleNamespace


class FakeQDialog:
    pass


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z=0.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class FakeQMessageBox:
    warnings = []

    @classmethod
    def warning(
        cls,
        *args,
        **kwargs,
    ):
        cls.warnings.append(
            args
        )


class FakeStatusBar:
    def __init__(self):
        self.message = ""

    def showMessage(
        self,
        message,
    ):
        self.message = message

    def clearMessage(self):
        self.message = ""


class FakeSelection:
    def __init__(self):
        self.objects = []
        self.observers = []

    def getSelection(self):
        return list(
            self.objects
        )

    def clearSelection(self):
        self.objects = []

    def addSelection(
        self,
        obj,
    ):
        self.objects.append(
            obj
        )

    def addObserver(
        self,
        observer,
    ):
        self.observers.append(
            observer
        )

    def removeObserver(
        self,
        observer,
    ):
        if observer in self.observers:
            self.observers.remove(
                observer
            )


status_bar = FakeStatusBar()
selection = FakeSelection()

fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.ActiveDocument = None
fake_freecad.Vector = FakeVector

fake_freecad_gui = types.ModuleType(
    "FreeCADGui"
)
fake_freecad_gui.Selection = selection
fake_freecad_gui.addCommand = (
    lambda *args, **kwargs: None
)
fake_freecad_gui.getMainWindow = (
    lambda: SimpleNamespace(
        statusBar=lambda: status_bar
    )
)

fake_part = types.ModuleType(
    "Part"
)

fake_pyside = types.ModuleType(
    "PySide"
)
fake_pyside.QtGui = SimpleNamespace(
    QDialog=FakeQDialog,
    QMessageBox=FakeQMessageBox,
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


from forgecad.fabrication import (
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.adapters.freecad.commands import (
    mirror_members as module,
)

# Other test modules may have imported mirror_members earlier with a
# different FreeCADGui test double. Make this file independent of test
# collection order by explicitly binding the module to these fixtures.
module.FreeCAD = fake_freecad
module.FreeCADGui = fake_freecad_gui
module.QtGui = fake_pyside.QtGui


def vector(
    x,
    y,
    z=0.0,
):
    return SimpleNamespace(
        x=float(
            x
        ),
        y=float(
            y
        ),
        z=float(
            z
        ),
    )


def reference(
    start,
    end,
):
    return SimpleNamespace(
        StartPoint=start,
        EndPoint=end,
    )


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def make_material():
    return Material(
        name="DOM Steel",
        density=7850.0,
        yield_strength=350.0,
    )


def make_member():
    return Member(
        start=Node(
            300.0,
            0.0,
            100.0,
        ),
        end=Node(
            500.0,
            400.0,
            300.0,
        ),
        profile=make_profile(),
        material=make_material(),
    )


def test_centerline_reference_accepts_start_and_end_points():
    obj = reference(
        vector(
            100,
            0,
        ),
        vector(
            100,
            1000,
        ),
    )

    assert module.is_centerline_reference(
        obj
    )


def test_centerline_nodes_come_from_selected_reference():
    obj = reference(
        vector(
            100,
            -500,
        ),
        vector(
            100,
            500,
        ),
    )

    start, end = (
        module.centerline_nodes_from_object(
            obj
        )
    )

    assert start == Node(
        100.0,
        -500.0,
        0.0,
    )

    assert end == Node(
        100.0,
        500.0,
        0.0,
    )


def test_mirror_member_uses_chosen_centerline(
    monkeypatch,
):
    source = make_member()

    source_object = SimpleNamespace(
        MemberID="M001",
        StartPoint=vector(
            300,
            0,
            100,
        ),
        EndPoint=vector(
            500,
            400,
            300,
        ),
    )

    monkeypatch.setattr(
        module,
        "structural_member_from_freecad_object",
        lambda obj: source,
    )

    created_points = []

    fake_draw_module = types.ModuleType(
        "forgecad.adapters.freecad.commands.draw_member_interactive"
    )

    def fake_get_or_create_node(
        document,
        point,
    ):
        created_points.append(
            point
        )

        return SimpleNamespace(
            Position=point
        )

    fake_draw_module.get_or_create_node = (
        fake_get_or_create_node
    )

    monkeypatch.setitem(
        sys.modules,
        (
            "forgecad.adapters.freecad.commands."
            "draw_member_interactive"
        ),
        fake_draw_module,
    )

    captured = {}

    def fake_create(
        document,
        start_node,
        end_node,
        profile=None,
        material=None,
    ):
        captured[
            "profile"
        ] = profile
        captured[
            "material"
        ] = material

        return (
            object(),
            "mirrored",
        )

    monkeypatch.setattr(
        module,
        "create_member_between_nodes",
        fake_create,
    )

    result = module.mirror_member_object(
        object(),
        source_object,
        Node(
            100.0,
            -1000.0,
            0.0,
        ),
        Node(
            100.0,
            1000.0,
            0.0,
        ),
    )

    assert result == "mirrored"

    assert created_points[
        0
    ].x == -100.0

    assert created_points[
        0
    ].y == 0.0

    assert created_points[
        1
    ].x == -300.0

    assert created_points[
        1
    ].y == 400.0

    assert captured[
        "profile"
    ] is source.profile

    assert captured[
        "material"
    ] is source.material


def test_three_source_members_produce_three_mirror_requests(
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        module,
        "mirror_member_object",
        lambda document, obj, start, end: (
            calls.append(
                obj
            )
            or f"mirror-{obj}"
        ),
    )

    centerline = reference(
        vector(
            0,
            -1000,
        ),
        vector(
            0,
            1000,
        ),
    )

    result = module.mirror_member_objects(
        object(),
        [
            "M001",
            "M002",
            "M003",
        ],
        centerline,
    )

    assert calls == [
        "M001",
        "M002",
        "M003",
    ]

    assert result == (
        "mirror-M001",
        "mirror-M002",
        "mirror-M003",
    )


def test_interactive_tool_captures_members_before_centerline_click():
    document = SimpleNamespace(
        Name="Doc",
    )

    members = (
        object(),
        object(),
        object(),
    )

    tool = (
        module.InteractiveMirrorMembersTool(
            document,
            members,
        )
    )

    assert tool.member_objects == members


def test_interactive_tool_registers_selection_observer():
    selection.observers = []

    document = SimpleNamespace(
        Name="Doc",
    )

    tool = (
        module.InteractiveMirrorMembersTool(
            document,
            [
                object(),
            ],
        )
    )

    tool.start()

    assert tool.running
    assert tool.observer in selection.observers
    assert "centerline" in (
        status_bar.message.lower()
    )

    tool.stop()

    assert tool.observer not in selection.observers
