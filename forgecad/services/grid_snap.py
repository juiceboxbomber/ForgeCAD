"""Pure grid-snapping helpers for ForgeCAD layout workflows."""


def validate_grid_spacing(
    spacing,
) -> float:
    """Return a positive grid spacing."""

    spacing = float(
        spacing
    )

    if spacing <= 0.0:
        raise ValueError(
            "Grid spacing must be greater than zero."
        )

    return spacing


def snap_coordinate_to_grid(
    value,
    spacing,
    origin=0.0,
) -> float:
    """Snap one coordinate to the nearest grid increment."""

    spacing = validate_grid_spacing(
        spacing
    )

    value = float(
        value
    )
    origin = float(
        origin
    )

    return (
        origin
        + round(
            (
                value
                - origin
            )
            / spacing
        )
        * spacing
    )


def snap_xy_coordinates(
    x,
    y,
    spacing,
    origin_x=0.0,
    origin_y=0.0,
) -> tuple[float, float]:
    """Snap XY coordinates to a common grid spacing."""

    return (
        snap_coordinate_to_grid(
            x,
            spacing,
            origin_x,
        ),
        snap_coordinate_to_grid(
            y,
            spacing,
            origin_y,
        ),
    )
