"""Tests for editable ForgeCAD workspace settings."""

import pytest

from forgecad import (
    ProjectType,
    project_module_for_type,
)
from forgecad.workspace_settings import (
    WorkspaceSettings,
)


def test_workspace_settings_from_chassis_defaults():
    module = project_module_for_type(
        ProjectType.CHASSIS
    )

    settings = WorkspaceSettings.from_defaults(
        module.workspace
    )

    assert settings.width_mm == 4000.0
    assert settings.height_mm == 2000.0
    assert settings.major_grid_mm == 100.0
    assert settings.minor_grid_mm == 25.0
    assert settings.grid_visible is True
    assert settings.snap_enabled is True


def test_workspace_settings_allow_project_customization():
    settings = WorkspaceSettings(
        width_mm=5000.0,
        height_mm=2400.0,
        major_grid_mm=200.0,
        minor_grid_mm=50.0,
        grid_visible=False,
        snap_enabled=False,
    )

    assert settings.width_mm == 5000.0
    assert settings.height_mm == 2400.0
    assert settings.major_grid_mm == 200.0
    assert settings.minor_grid_mm == 50.0
    assert settings.grid_visible is False
    assert settings.snap_enabled is False


@pytest.mark.parametrize(
    (
        "field_name",
        "value",
        "message",
    ),
    (
        (
            "width_mm",
            0.0,
            "Workspace width",
        ),
        (
            "height_mm",
            0.0,
            "Workspace height",
        ),
        (
            "major_grid_mm",
            0.0,
            "Major grid spacing",
        ),
        (
            "minor_grid_mm",
            0.0,
            "Minor grid spacing",
        ),
    ),
)
def test_workspace_settings_require_positive_dimensions(
    field_name,
    value,
    message,
):
    values = {
        "width_mm": 4000.0,
        "height_mm": 2000.0,
        "major_grid_mm": 100.0,
        "minor_grid_mm": 25.0,
    }

    values[
        field_name
    ] = value

    with pytest.raises(
        ValueError,
        match=message,
    ):
        WorkspaceSettings(
            **values
        )


def test_workspace_settings_reject_minor_grid_larger_than_major():
    with pytest.raises(
        ValueError,
        match="Minor grid spacing",
    ):
        WorkspaceSettings(
            width_mm=4000.0,
            height_mm=2000.0,
            major_grid_mm=25.0,
            minor_grid_mm=100.0,
        )
