"""Editable ForgeCAD display settings."""

from dataclasses import dataclass


def _validate_color(color, field_name):
    """Return a normalized RGB tuple with values from 0.0 to 1.0."""

    try:
        values = tuple(float(component) for component in color)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{field_name} must be an RGB color."
        ) from error

    if len(values) != 3:
        raise ValueError(
            f"{field_name} must contain exactly three RGB values."
        )

    if any(
        component < 0.0 or component > 1.0
        for component in values
    ):
        raise ValueError(
            f"{field_name} RGB values must be between 0.0 and 1.0."
        )

    return values


def _validate_line_width(value, field_name):
    """Return a positive line width."""

    value = float(value)

    if value <= 0.0:
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return value


@dataclass(frozen=True, slots=True)
class DisplaySettings:
    """Per-project visual styling for ForgeCAD reference geometry."""

    grid_color: tuple[float, float, float] = (0.55, 0.55, 0.55)
    grid_line_width: float = 1.0

    axis_color: tuple[float, float, float] = (0.90, 0.45, 0.10)
    axis_line_width: float = 2.0

    layout_line_color: tuple[float, float, float] = (1.0, 1.0, 0.0)
    layout_line_width: float = 3.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "grid_color",
            _validate_color(
                self.grid_color,
                "Grid color",
            ),
        )

        object.__setattr__(
            self,
            "axis_color",
            _validate_color(
                self.axis_color,
                "Axis color",
            ),
        )

        object.__setattr__(
            self,
            "layout_line_color",
            _validate_color(
                self.layout_line_color,
                "Layout line color",
            ),
        )

        object.__setattr__(
            self,
            "grid_line_width",
            _validate_line_width(
                self.grid_line_width,
                "Grid line width",
            ),
        )

        object.__setattr__(
            self,
            "axis_line_width",
            _validate_line_width(
                self.axis_line_width,
                "Axis line width",
            ),
        )

        object.__setattr__(
            self,
            "layout_line_width",
            _validate_line_width(
                self.layout_line_width,
                "Layout line width",
            ),
        )
