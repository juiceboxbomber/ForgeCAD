"""Tests for ForgeCAD parametric bent-tube document objects."""

import sys
import types


class FakeQuantity:
    """FreeCAD-like quantity exposing a Value attribute."""

    def __init__(
        self,
        value=0.0,
    ):
        self.Value = float(
            value
        )

    def __float__(
        self,
    ):
        return self.Value


class FakeVector:
    """Minimal FreeCAD.Vector replacement."""

    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.Vector = FakeVector

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "Part"
] = fake_part


from forgecad.fabrication import (
    Bend,
    BentTube,
    Material,
    StraightRun,
    TubeProfile,
)

import forgecad.adapters.freecad.bent_tube_object as bent_object


class FakeDocumentObject:
    """Minimal FeaturePython-like document object."""

    def __init__(
        self,
        name="ForgeCADBentTube",
    ):
        self.Name = name
        self.Label = name
        self.Proxy = None
        self.Shape = None

        self.ViewObject = types.SimpleNamespace(
            Proxy=None,
            Visibility=False,
            Deviation=0.5,
            AngularDeflection=28.5,
        )

        self._editor_modes = {}

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        if property_type in (
            "App::PropertyLength",
            "App::PropertyAngle",
        ):
            setattr(
                self,
                property_name,
                FakeQuantity(
                    0.0
                ),
            )
        elif property_type == "App::PropertyInteger":
            setattr(
                self,
                property_name,
                0,
            )
        elif property_type == "App::PropertyVector":
            setattr(
                self,
                property_name,
                FakeVector(
                    0.0,
                    0.0,
                    0.0,
                ),
            )
        elif property_type == "App::PropertyEnumeration":
            setattr(
                self,
                property_name,
                [],
            )
        else:
            setattr(
                self,
                property_name,
                ""

            )

    def __setattr__(
        self,
        name,
        value,
    ):
        existing = self.__dict__.get(
            name
        )

        if isinstance(
            existing,
            FakeQuantity,
        ) and not isinstance(
            value,
            FakeQuantity,
        ):
            existing.Value = float(
                value
            )
            return

        object.__setattr__(
            self,
            name,
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


class FakeDocument:
    """Minimal FreeCAD document."""

    def __init__(
        self,
    ):
        self.objects = []
        self.recompute_count = 0

    def addObject(
        self,
        type_name,
        name,
    ):
        obj = FakeDocumentObject(
            name
        )
        self.objects.append(
            obj
        )
        return obj

    def recompute(
        self,
    ):
        self.recompute_count += 1


def _material():
    return Material(
        name="A513 Type 5 DOM",
        density=7850.0,
        yield_strength=350.0,
    )


def _profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.048,
    )


def _tube():
    return BentTube(
        straight_runs=(
            StraightRun(
                500.0
            ),
            StraightRun(
                600.0
            ),
            StraightRun(
                700.0
            ),
        ),
        bends=(
            Bend(
                angle_degrees=90.0,
                centerline_radius=100.0,
                rotation_degrees=0.0,
            ),
            Bend(
                angle_degrees=45.0,
                centerline_radius=125.0,
                rotation_degrees=90.0,
            ),
        ),
        profile=_profile(),
        material=_material(),
    )


def _stub_shape_builder(
    monkeypatch,
):
    calls = []

    def fake_builder(
        tube,
        start_point,
        initial_direction,
        initial_bend_normal,
    ):
        calls.append(
            (
                tube,
                start_point,
                initial_direction,
                initial_bend_normal,
            )
        )

        return (
            "fake-shape",
            "fake-centerline",
        )

    monkeypatch.setattr(
        bent_object,
        "build_bent_tube_shape",
        fake_builder,
    )

    return calls


def test_proxy_creates_dynamic_run_and_bend_properties(
    monkeypatch,
):
    _stub_shape_builder(
        monkeypatch
    )

    obj = FakeDocumentObject()

    proxy = bent_object.BentTubeProxy(
        obj,
        _tube(),
    )

    assert obj.Proxy is proxy

    assert hasattr(
        obj,
        "Run1Length",
    )
    assert hasattr(
        obj,
        "Run2Length",
    )
    assert hasattr(
        obj,
        "Run3Length",
    )

    assert hasattr(
        obj,
        "Bend1Angle",
    )
    assert hasattr(
        obj,
        "Bend1Radius",
    )
    assert hasattr(
        obj,
        "Bend1Rotation",
    )

    assert hasattr(
        obj,
        "Bend2Angle",
    )
    assert hasattr(
        obj,
        "Bend2Radius",
    )
    assert hasattr(
        obj,
        "Bend2Rotation",
    )

    assert obj.BendCount == 2


def test_proxy_rebuilds_bent_tube_from_properties(
    monkeypatch,
):
    calls = _stub_shape_builder(
        monkeypatch
    )

    obj = FakeDocumentObject()

    proxy = bent_object.BentTubeProxy(
        obj,
        _tube(),
    )

    obj.Run2Length = 800.0
    obj.Bend2Angle = 60.0
    obj.Bend2Radius = 150.0
    obj.Bend2Rotation = 120.0

    proxy.update_shape(
        obj
    )

    rebuilt = calls[
        -1
    ][
        0
    ]

    assert rebuilt.straight_runs[
        1
    ].length_mm == 800.0

    assert rebuilt.bends[
        1
    ].angle_degrees == 60.0

    assert rebuilt.bends[
        1
    ].centerline_radius == 150.0

    assert rebuilt.bends[
        1
    ].rotation_degrees == 120.0


def test_update_shape_passes_document_orientation(
    monkeypatch,
):
    calls = _stub_shape_builder(
        monkeypatch
    )

    obj = FakeDocumentObject()

    proxy = bent_object.BentTubeProxy(
        obj,
        _tube(),
    )

    obj.StartPoint = FakeVector(
        10.0,
        20.0,
        30.0,
    )

    obj.InitialDirection = FakeVector(
        0.0,
        1.0,
        0.0,
    )

    obj.InitialBendNormal = FakeVector(
        0.0,
        0.0,
        1.0,
    )

    proxy.update_shape(
        obj
    )

    (
        _tube_value,
        start_point,
        direction,
        normal,
    ) = calls[
        -1
    ]

    assert (
        start_point.x,
        start_point.y,
        start_point.z,
    ) == (
        10.0,
        20.0,
        30.0,
    )

    assert (
        direction.x,
        direction.y,
        direction.z,
    ) == (
        0.0,
        1.0,
        0.0,
    )

    assert (
        normal.x,
        normal.y,
        normal.z,
    ) == (
        0.0,
        0.0,
        1.0,
    )


def test_editing_geometry_property_regenerates_shape(
    monkeypatch,
):
    calls = _stub_shape_builder(
        monkeypatch
    )

    obj = FakeDocumentObject()

    proxy = bent_object.BentTubeProxy(
        obj,
        _tube(),
    )

    initial_count = len(
        calls
    )

    proxy._ready = True

    proxy.onChanged(
        obj,
        "Bend1Angle",
    )

    assert len(
        calls
    ) == (
        initial_count + 1
    )



def test_explicit_design_joint_order_overrides_legacy_joint_when_prepending():
    """
    An explicit numbered design-joint path is authoritative.

    A legacy DesignJointNode may remain on older converted bends for backward
    compatibility, but it must not be inserted ahead of an explicitly supplied
    prepend order.
    """

    obj = FakeDocumentObject()

    legacy_first_joint = object()
    new_prepend_joint = object()
    existing_second_joint = object()

    # Simulate an existing converted bent tube that still carries the legacy
    # single-joint property as well as numbered topology.
    obj.DesignJointNode = legacy_first_joint
    obj.DesignJointNode1 = legacy_first_joint
    obj.DesignJointNode2 = existing_second_joint

    bent_object.ensure_bent_tube_design_joint_links(
        obj,
        (
            new_prepend_joint,
            legacy_first_joint,
            existing_second_joint,
        ),
    )

    assert (
        obj.DesignJointNode1
        is new_prepend_joint
    )

    assert (
        obj.DesignJointNode2
        is legacy_first_joint
    )

    assert (
        obj.DesignJointNode3
        is existing_second_joint
    )

def test_tube_name_updates_tree_label(
    monkeypatch,
):
    _stub_shape_builder(
        monkeypatch
    )

    obj = FakeDocumentObject()

    proxy = bent_object.BentTubeProxy(
        obj,
        _tube(),
    )

    proxy._ready = True

    obj.TubeName = (
        "Main Hoop"
    )

    proxy.onChanged(
        obj,
        "TubeName",
    )

    assert obj.Label == "Main Hoop"


def test_create_bent_tube_object_builds_initial_shape(
    monkeypatch,
):
    calls = _stub_shape_builder(
        monkeypatch
    )

    document = FakeDocument()

    obj = bent_object.create_bent_tube_object(
        document,
        _tube(),
    )

    assert obj.Proxy is not None
    assert obj.Shape == "fake-shape"
    assert len(
        calls
    ) == 1
    assert obj.Label == "Bent Tube"

def test_joint_derived_bend_radius_edit_preserves_fixed_nodes(
    monkeypatch,
):
    calls = _stub_shape_builder(
        monkeypatch
    )

    obj = FakeDocumentObject()

    proxy = bent_object.BentTubeProxy(
        obj,
        _tube(),
    )

    start_node = types.SimpleNamespace(
        Position=FakeVector(
            0.0,
            0.0,
            0.0,
        )
    )

    design_joint_node = types.SimpleNamespace(
        Position=FakeVector(
            1000.0,
            0.0,
            0.0,
        )
    )

    end_node = types.SimpleNamespace(
        Position=FakeVector(
            1000.0,
            1000.0,
            0.0,
        )
    )

    obj.StartNode = start_node
    obj.EndNode = end_node
    obj.DesignJointNode = (
        design_joint_node
    )

    obj.StartPoint = FakeVector(
        0.0,
        0.0,
        0.0,
    )

    obj.InitialDirection = FakeVector(
        1.0,
        0.0,
        0.0,
    )

    obj.InitialBendNormal = FakeVector(
        0.0,
        0.0,
        1.0,
    )

    obj.BendCount = 1

    obj.Run1Length = 900.0
    obj.Run2Length = 900.0

    obj.Bend1Angle = 90.0
    obj.Bend1Radius = 200.0
    obj.Bend1Rotation = 0.0

    original_sync = (
        bent_object.sync_bent_tube_end_node
    )

    sync_calls = []

    bent_object.sync_bent_tube_end_node = (
        lambda bent_tube_object,
        centerline: sync_calls.append(
            (
                bent_tube_object,
                centerline,
            )
        )
    )

    obj.Document = types.SimpleNamespace()

    proxy._ready = True

    try:
        proxy.onChanged(
            obj,
            "Bend1Radius",
        )

    finally:
        bent_object.sync_bent_tube_end_node = (
            original_sync
        )

    rebuilt = calls[
        -1
    ][
        0
    ]

    assert obj.Run1Length.Value == 800.0
    assert obj.Run2Length.Value == 800.0

    assert rebuilt.straight_runs[
        0
    ].length_mm == 800.0

    assert rebuilt.straight_runs[
        1
    ].length_mm == 800.0

    assert (
        start_node.Position.x,
        start_node.Position.y,
        start_node.Position.z,
    ) == (
        0.0,
        0.0,
        0.0,
    )

    assert (
        design_joint_node.Position.x,
        design_joint_node.Position.y,
        design_joint_node.Position.z,
    ) == (
        1000.0,
        0.0,
        0.0,
    )

    assert (
        end_node.Position.x,
        end_node.Position.y,
        end_node.Position.z,
    ) == (
        1000.0,
        1000.0,
        0.0,
    )

    assert sync_calls == []

def test_joint_derived_bend_rebuilds_when_end_node_moves(
    monkeypatch,
):
    calls = _stub_shape_builder(
        monkeypatch
    )

    obj = FakeDocumentObject()

    proxy = bent_object.BentTubeProxy(
        obj,
        _tube(),
    )

    start_node = types.SimpleNamespace(
        Position=FakeVector(
            0.0,
            0.0,
            0.0,
        )
    )

    design_joint_node = types.SimpleNamespace(
        Position=FakeVector(
            1000.0,
            0.0,
            0.0,
        )
    )

    end_node = types.SimpleNamespace(
        Position=FakeVector(
            1000.0,
            1000.0,
            0.0,
        )
    )

    obj.StartNode = start_node
    obj.EndNode = end_node
    obj.DesignJointNode = (
        design_joint_node
    )

    obj.StartPoint = FakeVector(
        0.0,
        0.0,
        0.0,
    )

    obj.InitialDirection = FakeVector(
        1.0,
        0.0,
        0.0,
    )

    obj.InitialBendNormal = FakeVector(
        0.0,
        0.0,
        1.0,
    )

    obj.BendCount = 1

    obj.Run1Length = 900.0
    obj.Run2Length = 900.0

    obj.Bend1Angle = 90.0
    obj.Bend1Radius = 100.0
    obj.Bend1Rotation = 0.0

    obj.Document = types.SimpleNamespace()

    proxy._ready = True
    proxy._geometry_dirty = False

    initial_count = len(
        calls
    )

    # Move only the outer EndNode.
    #
    # The theoretical joint stays at (1000, 0, 0), but the
    # second leg now points diagonally toward (1500, 1000, 0).
    end_node.Position = FakeVector(
        1500.0,
        1000.0,
        0.0,
    )

    proxy.execute(
        obj
    )

    assert len(
        calls
    ) == (
        initial_count + 1
    )

    assert (
        end_node.Position.x,
        end_node.Position.y,
        end_node.Position.z,
    ) == (
        1500.0,
        1000.0,
        0.0,
    )

    assert (
        design_joint_node.Position.x,
        design_joint_node.Position.y,
        design_joint_node.Position.z,
    ) == (
        1000.0,
        0.0,
        0.0,
    )

    # Moving the endpoint changes the joint angle, so the
    # physical bend angle must no longer remain 90 degrees.
    assert (
        obj.Bend1Angle.Value
        != 90.0
    )

    # The second run must also be recalculated from the
    # new fixed endpoint geometry.
    assert (
        obj.Run2Length.Value
        != 900.0
    )

def test_joint_derived_bend_rebuilds_when_start_node_moves(
    monkeypatch,
):
    calls = _stub_shape_builder(
        monkeypatch
    )

    obj = FakeDocumentObject()

    proxy = bent_object.BentTubeProxy(
        obj,
        _tube(),
    )

    start_node = types.SimpleNamespace(
        Position=FakeVector(
            0.0,
            0.0,
            0.0,
        )
    )

    design_joint_node = types.SimpleNamespace(
        Position=FakeVector(
            1000.0,
            0.0,
            0.0,
        )
    )

    end_node = types.SimpleNamespace(
        Position=FakeVector(
            1000.0,
            1000.0,
            0.0,
        )
    )

    obj.StartNode = start_node
    obj.EndNode = end_node
    obj.DesignJointNode = (
        design_joint_node
    )

    obj.StartPoint = FakeVector(
        0.0,
        0.0,
        0.0,
    )

    obj.InitialDirection = FakeVector(
        1.0,
        0.0,
        0.0,
    )

    obj.InitialBendNormal = FakeVector(
        0.0,
        0.0,
        1.0,
    )

    obj.BendCount = 1

    obj.Run1Length = 900.0
    obj.Run2Length = 900.0

    obj.Bend1Angle = 90.0
    obj.Bend1Radius = 100.0
    obj.Bend1Rotation = 0.0

    obj.Document = types.SimpleNamespace()

    proxy._ready = True
    proxy._geometry_dirty = False

    proxy._last_joint_geometry = (
        proxy._joint_geometry_signature(
            obj
        )
    )

    initial_count = len(
        calls
    )

    start_node.Position = FakeVector(
        0.0,
        500.0,
        0.0,
    )

    proxy.execute(
        obj
    )

    assert len(
        calls
    ) == (
        initial_count + 1
    )

    assert (
        start_node.Position.x,
        start_node.Position.y,
        start_node.Position.z,
    ) == (
        0.0,
        500.0,
        0.0,
    )

    assert (
        end_node.Position.x,
        end_node.Position.y,
        end_node.Position.z,
    ) == (
        1000.0,
        1000.0,
        0.0,
    )

    assert (
        design_joint_node.Position.x,
        design_joint_node.Position.y,
        design_joint_node.Position.z,
    ) == (
        1000.0,
        0.0,
        0.0,
    )

    assert (
        obj.Bend1Angle.Value
        != 90.0
    )

    assert (
        obj.Run1Length.Value
        != 900.0
    )


def test_joint_derived_bend_rebuilds_when_design_joint_moves(
    monkeypatch,
):
    calls = _stub_shape_builder(
        monkeypatch
    )

    obj = FakeDocumentObject()

    proxy = bent_object.BentTubeProxy(
        obj,
        _tube(),
    )

    start_node = types.SimpleNamespace(
        Position=FakeVector(
            0.0,
            0.0,
            0.0,
        )
    )

    design_joint_node = types.SimpleNamespace(
        Position=FakeVector(
            1000.0,
            0.0,
            0.0,
        )
    )

    end_node = types.SimpleNamespace(
        Position=FakeVector(
            1000.0,
            1000.0,
            0.0,
        )
    )

    obj.StartNode = start_node
    obj.EndNode = end_node
    obj.DesignJointNode = (
        design_joint_node
    )

    obj.StartPoint = FakeVector(
        0.0,
        0.0,
        0.0,
    )

    obj.InitialDirection = FakeVector(
        1.0,
        0.0,
        0.0,
    )

    obj.InitialBendNormal = FakeVector(
        0.0,
        0.0,
        1.0,
    )

    obj.BendCount = 1

    obj.Run1Length = 900.0
    obj.Run2Length = 900.0

    obj.Bend1Angle = 90.0
    obj.Bend1Radius = 100.0
    obj.Bend1Rotation = 0.0

    obj.Document = types.SimpleNamespace()

    proxy._ready = True
    proxy._geometry_dirty = False

    proxy._last_joint_geometry = (
        proxy._joint_geometry_signature(
            obj
        )
    )

    initial_count = len(
        calls
    )

    design_joint_node.Position = FakeVector(
        900.0,
        100.0,
        0.0,
    )

    proxy.execute(
        obj
    )

    assert len(
        calls
    ) == (
        initial_count + 1
    )

    assert (
        start_node.Position.x,
        start_node.Position.y,
        start_node.Position.z,
    ) == (
        0.0,
        0.0,
        0.0,
    )

    assert (
        end_node.Position.x,
        end_node.Position.y,
        end_node.Position.z,
    ) == (
        1000.0,
        1000.0,
        0.0,
    )

    assert (
        design_joint_node.Position.x,
        design_joint_node.Position.y,
        design_joint_node.Position.z,
    ) == (
        900.0,
        100.0,
        0.0,
    )

    assert (
        obj.Bend1Angle.Value
        != 90.0
    )

    assert (
        obj.Run1Length.Value
        != 900.0
    )

    assert (
        obj.Run2Length.Value
        != 900.0
    )

