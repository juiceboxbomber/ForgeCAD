"""FreeCAD command for creating a ForgeCAD reference plane."""

import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui

from forgecad.adapters.freecad.dialogs.create_reference_plane import (
    CreateReferencePlaneDialog,
)
from forgecad.adapters.freecad.reference_plane_store import (
    find_reference_plane_object,
    save_reference_plane,
)


COMMAND_NAME = (
    "ForgeCAD_CreateReferencePlane"
)

DEFAULT_PLANE_SIZE = 1000.0


def plane_shape(
    plane,
    size=DEFAULT_PLANE_SIZE,
):
    """Return a square planar face representing a reference plane."""

    size = float(
        size
    )

    if size <= 0.0:
        raise ValueError(
            "Reference plane display size must be positive."
        )

    half = (
        size / 2.0
    )

    offset = float(
        plane.offset
    )

    orientation = (
        plane.orientation.value
    )

    if orientation == "XY":
        points = (
            FreeCAD.Vector(
                -half,
                -half,
                offset,
            ),
            FreeCAD.Vector(
                half,
                -half,
                offset,
            ),
            FreeCAD.Vector(
                half,
                half,
                offset,
            ),
            FreeCAD.Vector(
                -half,
                half,
                offset,
            ),
        )

    elif orientation == "XZ":
        points = (
            FreeCAD.Vector(
                -half,
                offset,
                -half,
            ),
            FreeCAD.Vector(
                half,
                offset,
                -half,
            ),
            FreeCAD.Vector(
                half,
                offset,
                half,
            ),
            FreeCAD.Vector(
                -half,
                offset,
                half,
            ),
        )

    else:
        points = (
            FreeCAD.Vector(
                offset,
                -half,
                -half,
            ),
            FreeCAD.Vector(
                offset,
                half,
                -half,
            ),
            FreeCAD.Vector(
                offset,
                half,
                half,
            ),
            FreeCAD.Vector(
                offset,
                -half,
                half,
            ),
        )

    wire = Part.makePolygon(
        [
            *points,
            points[
                0
            ],
        ]
    )

    return Part.Face(
        wire
    )


def apply_reference_plane_display(
    obj,
    plane,
):
    """Assign selectable reference-plane geometry and display styling."""

    obj.Shape = plane_shape(
        plane
    )

    view = getattr(
        obj,
        "ViewObject",
        None,
    )

    if view is None:
        return obj

    try:
        view.ShapeColor = (
            0.35,
            0.65,
            1.00,
        )
    except Exception:
        pass

    try:
        view.LineColor = (
            0.15,
            0.35,
            0.80,
        )
    except Exception:
        pass

    try:
        view.Transparency = 75
    except Exception:
        pass

    try:
        view.DisplayMode = (
            "Flat Lines"
        )
    except Exception:
        pass

    try:
        view.Selectable = True
    except Exception:
        pass

    return obj


def create_reference_plane(
    document,
    plane,
):
    """Persist and render one ForgeCAD reference plane."""

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    existing = (
        find_reference_plane_object(
            document,
            plane.name,
        )
    )

    if existing is not None:
        raise ValueError(
            f'A reference plane named "{plane.name}" already exists.'
        )

    obj = save_reference_plane(
        document,
        plane,
    )

    apply_reference_plane_display(
        obj,
        plane,
    )

    document.recompute()

    return obj


class CreateReferencePlaneCommand:
    """Create a persistent selectable ForgeCAD reference plane."""

    def GetResources(
        self,
    ):
        return {
            "MenuText":
                "Create Reference Plane",
            "ToolTip": (
                "Create an axis-aligned ForgeCAD reference plane "
                "at a specified offset"
            ),
        }

    def Activated(
        self,
    ):
        document = (
            FreeCAD.ActiveDocument
        )

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Document",
                (
                    "Open or create a ForgeCAD "
                    "project first."
                ),
            )
            return

        dialog = (
            CreateReferencePlaneDialog(
                FreeCADGui.getMainWindow()
            )
        )

        if (
            dialog.exec_()
            != QtGui.QDialog.Accepted
        ):
            return

        try:
            plane = (
                dialog.reference_plane()
            )

            obj = create_reference_plane(
                document,
                plane,
            )

        except (
            ValueError,
            TypeError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Reference Plane Creation Failed",
                str(
                    error
                ),
            )
            return

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.Selection.addSelection(
            obj
        )

        try:
            FreeCADGui.activeDocument().activeView().fitAll()
        except Exception:
            pass

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Create Reference Plane command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        CreateReferencePlaneCommand(),
    )
