"""Tests for ForgeCAD project-module definitions."""

import pytest

from forgecad import (
    ProjectType,
    WorkspaceDefaults,
    project_module_for_type,
)


def test_general_fabrication_module_has_layout_workflow():
    module = project_module_for_type(
        ProjectType.GENERAL_FABRICATION
    )

    assert module.display_name == "General Fabrication"
    assert module.workflow_stages[0] == "Layout"
    assert module.workspace.major_grid_mm == 100.0
    assert module.workspace.minor_grid_mm == 25.0


def test_chassis_module_has_base_layout_workflow():
    module = project_module_for_type(
        ProjectType.CHASSIS
    )

    assert module.display_name == "Chassis"
    assert module.workflow_stages[0] == "Base Layout"
    assert "Crossmembers" in module.workflow_stages
    assert module.workspace.width_mm == 4000.0
    assert module.workspace.height_mm == 2000.0


def test_roll_cage_module_includes_bends():
    module = project_module_for_type(
        ProjectType.ROLL_CAGE
    )

    assert module.display_name == "Roll Cage"
    assert "Main Hoop" in module.workflow_stages
    assert "Bends" in module.workflow_stages
    assert module.workspace.width_mm == 2500.0
    assert module.workspace.height_mm == 2500.0


def test_project_module_lookup_accepts_project_type_value():
    module = project_module_for_type(
        "chassis"
    )

    assert module.project_type == ProjectType.CHASSIS


def test_workspace_rejects_minor_grid_larger_than_major():
    with pytest.raises(
        ValueError,
        match="Minor grid spacing",
    ):
        WorkspaceDefaults(
            width_mm=1000.0,
            height_mm=1000.0,
            major_grid_mm=25.0,
            minor_grid_mm=100.0,
        )
