"""Tests for editable ForgeCAD display settings."""

import pytest

from forgecad.display_settings import DisplaySettings


def test_display_settings_have_high_contrast_defaults():
    settings = DisplaySettings()

    assert settings.grid_color == (0.55, 0.55, 0.55)
    assert settings.grid_line_width == 1.0
    assert settings.axis_color == (0.90, 0.45, 0.10)
    assert settings.axis_line_width == 2.0
    assert settings.layout_line_color == (1.0, 1.0, 0.0)
    assert settings.layout_line_width == 3.0


def test_display_settings_allow_custom_colors_and_widths():
    settings = DisplaySettings(
        grid_color=(0.2, 0.2, 0.2),
        grid_line_width=0.5,
        axis_color=(1.0, 0.0, 0.0),
        axis_line_width=4.0,
        layout_line_color=(0.0, 1.0, 1.0),
        layout_line_width=5.0,
    )

    assert settings.grid_color == (0.2, 0.2, 0.2)
    assert settings.grid_line_width == 0.5
    assert settings.axis_color == (1.0, 0.0, 0.0)
    assert settings.axis_line_width == 4.0
    assert settings.layout_line_color == (0.0, 1.0, 1.0)
    assert settings.layout_line_width == 5.0


@pytest.mark.parametrize(
    "field_name",
    (
        "grid_line_width",
        "axis_line_width",
        "layout_line_width",
    ),
)
def test_display_settings_require_positive_line_widths(field_name):
    values = {
        "grid_line_width": 1.0,
        "axis_line_width": 2.0,
        "layout_line_width": 3.0,
    }

    values[field_name] = 0.0

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        DisplaySettings(**values)


def test_display_settings_reject_color_outside_rgb_range():
    with pytest.raises(
        ValueError,
        match="between 0.0 and 1.0",
    ):
        DisplaySettings(
            layout_line_color=(1.2, 0.5, 0.0)
        )


def test_display_settings_reject_wrong_color_length():
    with pytest.raises(
        ValueError,
        match="exactly three",
    ):
        DisplaySettings(
            grid_color=(0.5, 0.5)
        )
