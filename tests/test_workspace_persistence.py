"""Tests for persistent ForgeCAD workspace settings."""

import sys
import types


class FakeVector:
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

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "FreeCADGui"
] = types.ModuleType(
    "FreeCADGui"
)
fake_part = types.ModuleType(
    "Part"
)

fake_part.makeLine = (
    lambda start, end: (
        "line",
        start,
        end,
    )
)

fake_part.makeCompound = (
    lambda shapes: (
        "compound",
        tuple(
            shapes
        ),
    )
)

sys.modules[
    "Part"
] = fake_part


from forgecad import (
    ProjectType,
)
from forgecad.adapters.freecad.workspace import (
    project_type_for_document,
    workspace_settings_from_object,
)


class FakeWorkspace:
    ProjectType = "chassis"
    WorkspaceWidth = 5000.0
    WorkspaceHeight = 2400.0
    MajorGridSpacing = 200.0
    MinorGridSpacing = 50.0
    GridVisible = False
    SnapEnabled = False


class FakeRoot:
    ProjectType = "roll_cage"


class FakeDocument:
    def __init__(
        self,
        workspace=None,
        root=None,
    ):
        self.workspace = workspace
        self.root = root

    def getObject(
        self,
        name,
    ):
        if name == "ForgeCADWorkspace":
            return self.workspace

        if name == "ForgeCADProject":
            return self.root

        return None


def test_workspace_settings_are_loaded_from_persistent_object():
    settings = workspace_settings_from_object(
        FakeWorkspace()
    )

    assert settings.width_mm == 5000.0
    assert settings.height_mm == 2400.0
    assert settings.major_grid_mm == 200.0
    assert settings.minor_grid_mm == 50.0
    assert settings.grid_visible is False
    assert settings.snap_enabled is False


def test_document_project_type_prefers_workspace_metadata():
    document = FakeDocument(
        workspace=FakeWorkspace(),
        root=FakeRoot(),
    )

    assert (
        project_type_for_document(
            document
        )
        == ProjectType.CHASSIS
    )


def test_document_project_type_falls_back_to_root():
    document = FakeDocument(
        root=FakeRoot()
    )

    assert (
        project_type_for_document(
            document
        )
        == ProjectType.ROLL_CAGE
    )


def test_document_project_type_defaults_to_general():
    document = FakeDocument()

    assert (
        project_type_for_document(
            document
        )
        == ProjectType.GENERAL_FABRICATION
    )
