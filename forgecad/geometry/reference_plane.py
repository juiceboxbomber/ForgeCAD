"""ForgeCAD reference-plane geometry."""

from dataclasses import dataclass
from enum import Enum

from forgecad.geometry.point import (
    Point3D,
)
from forgecad.geometry.vector import (
    Vector3D,
)


class ReferencePlaneOrientation(
    str,
    Enum,
):
    """Supported axis-aligned reference-plane orientations."""

    XY = "XY"
    XZ = "XZ"
    YZ = "YZ"


@dataclass(
    frozen=True,
    slots=True,
)
class ReferencePlane:
    """
    Persistent geometric definition of a ForgeCAD reference plane.

    Offset is measured along the plane normal from the global origin.
    """

    name: str
    orientation: ReferencePlaneOrientation
    offset: float = 0.0

    def __post_init__(
        self,
    ):
        name = str(
            self.name
        ).strip()

        if not name:
            raise ValueError(
                "Reference plane requires a name."
            )

        orientation = (
            self.orientation
        )

        if not isinstance(
            orientation,
            ReferencePlaneOrientation,
        ):
            try:
                orientation = (
                    ReferencePlaneOrientation(
                        str(
                            orientation
                        ).upper()
                    )
                )
            except ValueError as error:
                raise ValueError(
                    "Reference plane orientation must be XY, XZ, or YZ."
                ) from error

        offset = float(
            self.offset
        )

        object.__setattr__(
            self,
            "name",
            name,
        )

        object.__setattr__(
            self,
            "orientation",
            orientation,
        )

        object.__setattr__(
            self,
            "offset",
            offset,
        )

    @property
    def normal(
        self,
    ):
        """Return the plane's positive global-axis normal."""

        if (
            self.orientation
            == ReferencePlaneOrientation.XY
        ):
            return Vector3D(
                0.0,
                0.0,
                1.0,
            )

        if (
            self.orientation
            == ReferencePlaneOrientation.XZ
        ):
            return Vector3D(
                0.0,
                1.0,
                0.0,
            )

        return Vector3D(
            1.0,
            0.0,
            0.0,
        )

    @property
    def origin(
        self,
    ):
        """Return a point lying on the plane."""

        if (
            self.orientation
            == ReferencePlaneOrientation.XY
        ):
            return Point3D(
                0.0,
                0.0,
                self.offset,
            )

        if (
            self.orientation
            == ReferencePlaneOrientation.XZ
        ):
            return Point3D(
                0.0,
                self.offset,
                0.0,
            )

        return Point3D(
            self.offset,
            0.0,
            0.0,
        )
    