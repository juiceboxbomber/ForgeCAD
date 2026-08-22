"""Interactive FreeCAD command for splitting one straight ForgeCAD member."""

import math

import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui

from forgecad.geometry import (
    Point3D,
)
from forgecad.adapters.freecad.member_split_adapter import (
    split_member_object,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    structural_member_from_freecad_object,
)


COMMAND_NAME = "ForgeCAD_SplitMember"

SNAP_DISTANCE_PIXELS = 20.0

PREVIEW_OBJECT_NAME = (
    "ForgeCADSplitPreview"
)

PREVIEW_MIN_HALF_LENGTH = 30.0
PREVIEW_OD_MARGIN = 8.0

_active_tool = None


def is_forgecad_member(
    obj,
):
    """Return True for a generated ForgeCAD straight-member object."""

    if obj is None:
        return False

    return all(
        hasattr(
            obj,
            property_name,
        )
        for property_name in (
            "MemberID",
            "StartPoint",
            "EndPoint",
        )
    )


def selected_member():
    """Return exactly one selected ForgeCAD straight member."""

    selection = list(
        FreeCADGui.Selection.getSelection()
    )

    if len(
        selection
    ) != 1:
        return None

    obj = selection[
        0
    ]

    if not is_forgecad_member(
        obj
    ):
        return None

    return obj


def point_from_vector(
    vector,
):
    """Return a Point3D from a FreeCAD-like vector."""

    return Point3D(
        float(
            vector.x
        ),
        float(
            vector.y
        ),
        float(
            vector.z
        ),
    )


def member_centerline(
    member_object,
):
    """Return the selected member's start/end centerline points."""

    if not is_forgecad_member(
        member_object
    ):
        raise ValueError(
            "Split Member requires one straight ForgeCAD member."
        )

    return (
        point_from_vector(
            member_object.StartPoint
        ),
        point_from_vector(
            member_object.EndPoint
        ),
    )


def screen_point_on_segment(
    view,
    position,
    start,
    end,
):
    """
    Return the exact 3D segment point nearest the mouse.

    The nearest location is chosen in screen space, then interpolated on
    the real 3D member centerline.
    """

    if (
        view is None
        or position is None
    ):
        return (
            None,
            None,
            None,
        )

    try:
        start_screen = (
            view.getPointOnScreen(
                FreeCAD.Vector(
                    start.x,
                    start.y,
                    start.z,
                )
            )
        )

        end_screen = (
            view.getPointOnScreen(
                FreeCAD.Vector(
                    end.x,
                    end.y,
                    end.z,
                )
            )
        )

    except Exception:
        return (
            None,
            None,
            None,
        )

    start_x = float(
        start_screen[
            0
        ]
    )
    start_y = float(
        start_screen[
            1
        ]
    )

    end_x = float(
        end_screen[
            0
        ]
    )
    end_y = float(
        end_screen[
            1
        ]
    )

    mouse_x = float(
        position[
            0
        ]
    )
    mouse_y = float(
        position[
            1
        ]
    )

    segment_x = (
        end_x
        - start_x
    )

    segment_y = (
        end_y
        - start_y
    )

    length_squared = (
        segment_x
        * segment_x
        + segment_y
        * segment_y
    )

    if length_squared <= 1e-12:
        return (
            None,
            None,
            None,
        )

    parameter = (
        (
            (
                mouse_x
                - start_x
            )
            * segment_x
            + (
                mouse_y
                - start_y
            )
            * segment_y
        )
        / length_squared
    )

    parameter = max(
        0.0,
        min(
            1.0,
            parameter,
        ),
    )

    snap_x = (
        start_x
        + parameter
        * segment_x
    )

    snap_y = (
        start_y
        + parameter
        * segment_y
    )

    distance = math.hypot(
        snap_x
        - mouse_x,
        snap_y
        - mouse_y,
    )

    point = Point3D(
        start.x
        + parameter
        * (
            end.x
            - start.x
        ),
        start.y
        + parameter
        * (
            end.y
            - start.y
        ),
        start.z
        + parameter
        * (
            end.z
            - start.z
        ),
    )

    return (
        point,
        distance,
        parameter,
    )


def preview_half_length_for_member(
    member_object,
):
    """
    Return a preview half-length that extends beyond the tube outside radius.

    The marker spans both sides of the member centerline, so each end is
    visible outside the solid tube. A conservative fallback is used when
    profile information cannot be reconstructed.
    """

    try:
        member = (
            structural_member_from_freecad_object(
                member_object
            )
        )

        outside_diameter = float(
            member.profile.outside_diameter
        )

    except Exception:
        return PREVIEW_MIN_HALF_LENGTH

    return max(
        PREVIEW_MIN_HALF_LENGTH,
        (
            outside_diameter
            * 0.5
            + PREVIEW_OD_MARGIN
        ),
    )


def perpendicular_unit_vector(
    start,
    end,
):
    """
    Return a stable 3D unit vector perpendicular to a member centerline.

    XY members receive an XY-plane perpendicular, which is especially
    useful in normal chassis top views. Near-vertical members fall back
    to a horizontal X direction.
    """

    dx = float(
        end.x
        - start.x
    )

    dy = float(
        end.y
        - start.y
    )

    dz = float(
        end.z
        - start.z
    )

    length = math.sqrt(
        dx * dx
        + dy * dy
        + dz * dz
    )

    if length <= 1e-12:
        raise ValueError(
            "Cannot preview a zero-length member."
        )

    # Cross member direction with global Z. This produces (-dy, dx, 0)
    # and keeps the marker visible in ordinary XY/top chassis views.
    px = dy
    py = -dx
    pz = 0.0

    perpendicular_length = math.sqrt(
        px * px
        + py * py
        + pz * pz
    )

    if perpendicular_length <= 1e-12:
        # Member is effectively parallel to Z. Use global X, which is
        # perpendicular to a vertical member.
        return (
            1.0,
            0.0,
            0.0,
        )

    return (
        px
        / perpendicular_length,
        py
        / perpendicular_length,
        pz
        / perpendicular_length,
    )


def preview_line_endpoints(
    point,
    start,
    end,
    half_length,
):
    """Return endpoints of the perpendicular split-preview line."""

    ux, uy, uz = (
        perpendicular_unit_vector(
            start,
            end,
        )
    )

    return (
        Point3D(
            point.x
            - ux
            * half_length,
            point.y
            - uy
            * half_length,
            point.z
            - uz
            * half_length,
        ),
        Point3D(
            point.x
            + ux
            * half_length,
            point.y
            + uy
            * half_length,
            point.z
            + uz
            * half_length,
        ),
    )


class InteractiveSplitMemberTool:
    """Choose one split position along a preselected straight member."""

    def __init__(
        self,
        document,
        member_object,
    ):
        self.document = document
        self.member_object = (
            member_object
        )

        (
            self.start_point,
            self.end_point,
        ) = member_centerline(
            member_object
        )

        self.preview_half_length = (
            preview_half_length_for_member(
                member_object
            )
        )

        self.view = None
        self.status_bar = None

        self.mouse_callback = None
        self.move_callback = None
        self.keyboard_callback = None

        self.preview_object = None
        self.current_split_point = None

    def start(
        self,
    ):
        """Start interactive split-position selection."""

        self.view = (
            FreeCADGui.activeDocument()
            .activeView()
        )

        self.status_bar = (
            FreeCADGui.getMainWindow()
            .statusBar()
        )

        self.mouse_callback = (
            self.view.addEventCallback(
                "SoMouseButtonEvent",
                self.on_mouse_event,
            )
        )

        self.move_callback = (
            self.view.addEventCallback(
                "SoLocation2Event",
                self.on_mouse_move,
            )
        )

        self.keyboard_callback = (
            self.view.addEventCallback(
                "SoKeyboardEvent",
                self.on_keyboard_event,
            )
        )

        self.show_status(
            "ForgeCAD Split Member: "
            "move along the selected member and click the split point. "
            "Esc: Cancel."
        )

    def show_status(
        self,
        message,
    ):
        """Show information in the FreeCAD status bar."""

        if self.status_bar is not None:
            self.status_bar.showMessage(
                message
            )

    def _remove_view_callback(
        self,
        event_name,
        callback,
    ):
        """Safely remove one viewport callback."""

        if (
            self.view is None
            or callback is None
        ):
            return

        try:
            self.view.removeEventCallback(
                event_name,
                callback,
            )
        except Exception:
            pass

    def remove_preview(
        self,
    ):
        """Remove the temporary split marker."""

        obj = self.preview_object
        self.preview_object = None

        if (
            obj is None
            or self.document is None
        ):
            return

        try:
            self.document.removeObject(
                obj.Name
            )
        except Exception:
            pass

        try:
            self.document.recompute()
        except Exception:
            pass

    def update_preview(
        self,
        point,
    ):
        """Move/create a perpendicular split-location indicator."""

        if point is None:
            self.remove_preview()
            return

        if self.preview_object is None:
            self.preview_object = (
                self.document.addObject(
                    "Part::Feature",
                    PREVIEW_OBJECT_NAME,
                )
            )

            self.preview_object.Label = (
                "Split Point Preview"
            )

            try:
                view = (
                    self.preview_object.ViewObject
                )

                view.Selectable = False

                view.LineColor = (
                    1.0,
                    1.0,
                    0.0,
                )

                view.LineWidth = 5.0

            except Exception:
                pass

        preview_start, preview_end = (
            preview_line_endpoints(
                point,
                self.start_point,
                self.end_point,
                self.preview_half_length,
            )
        )

        self.preview_object.Shape = (
            Part.makeLine(
                FreeCAD.Vector(
                    preview_start.x,
                    preview_start.y,
                    preview_start.z,
                ),
                FreeCAD.Vector(
                    preview_end.x,
                    preview_end.y,
                    preview_end.z,
                ),
            )
        )

        self.document.recompute()

    def stop(
        self,
    ):
        """Stop split mode and clean up callbacks/preview."""

        global _active_tool

        self._remove_view_callback(
            "SoMouseButtonEvent",
            self.mouse_callback,
        )

        self._remove_view_callback(
            "SoLocation2Event",
            self.move_callback,
        )

        self._remove_view_callback(
            "SoKeyboardEvent",
            self.keyboard_callback,
        )

        self.mouse_callback = None
        self.move_callback = None
        self.keyboard_callback = None

        self.remove_preview()

        self.current_split_point = None

        if self.status_bar is not None:
            try:
                self.status_bar.clearMessage()
            except Exception:
                pass

        self.status_bar = None
        self.view = None

        if _active_tool is self:
            _active_tool = None

    def resolve_split_point(
        self,
        position,
    ):
        """Return a valid interior split point near the member on screen."""

        (
            point,
            distance,
            parameter,
        ) = screen_point_on_segment(
            self.view,
            position,
            self.start_point,
            self.end_point,
        )

        if (
            point is None
            or distance is None
            or parameter is None
        ):
            return None

        if (
            distance
            > SNAP_DISTANCE_PIXELS
        ):
            return None

        # Avoid offering endpoints as valid split locations.
        if (
            parameter
            <= 1e-6
            or parameter
            >= (
                1.0
                - 1e-6
            )
        ):
            return None

        return point

    def on_mouse_move(
        self,
        event,
    ):
        """Update the split preview while the cursor moves."""

        position = event.get(
            "Position"
        )

        point = self.resolve_split_point(
            position
        )

        self.current_split_point = (
            point
        )

        self.update_preview(
            point
        )

        if point is None:
            self.show_status(
                "ForgeCAD Split Member: "
                "move onto the selected member centerline. "
                "Esc: Cancel."
            )
            return

        self.show_status(
            "ForgeCAD Split Member: "
            f"split at "
            f"({point.x:.3f}, "
            f"{point.y:.3f}, "
            f"{point.z:.3f}) - "
            "click to confirm. Esc: Cancel."
        )

    def on_mouse_event(
        self,
        event,
    ):
        """Commit the split on left-button press."""

        if event.get(
            "State"
        ) != "DOWN":
            return

        if event.get(
            "Button"
        ) != "BUTTON1":
            return

        position = event.get(
            "Position"
        )

        point = self.resolve_split_point(
            position
        )

        if point is None:
            return

        transaction_started = False

        try:
            if hasattr(
                self.document,
                "openTransaction",
            ):
                self.document.openTransaction(
                    "Split ForgeCAD Member"
                )

                transaction_started = True

            result = split_member_object(
                self.document,
                self.member_object,
                point,
            )

            if (
                transaction_started
                and hasattr(
                    self.document,
                    "commitTransaction",
                )
            ):
                self.document.commitTransaction()

        except (
            ValueError,
            KeyError,
            AttributeError,
        ) as error:
            if (
                transaction_started
                and hasattr(
                    self.document,
                    "abortTransaction",
                )
            ):
                try:
                    self.document.abortTransaction()
                except Exception:
                    pass

            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Split Member Failed",
                str(
                    error
                ),
            )
            return

        first_object = result[
            1
        ]

        second_object = result[
            3
        ]

        self.stop()

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.Selection.addSelection(
            first_object
        )

        FreeCADGui.Selection.addSelection(
            second_object
        )

        try:
            FreeCADGui.activeDocument().activeView().fitAll()
        except Exception:
            pass

    def on_keyboard_event(
        self,
        event,
    ):
        """Cancel Split Member with Escape."""

        if event.get(
            "State"
        ) != "DOWN":
            return

        if event.get(
            "Key"
        ) in (
            "ESCAPE",
            "ESC",
        ):
            self.stop()


class SplitMemberCommand:
    """Interactively split one selected straight ForgeCAD member."""

    def GetResources(
        self,
    ):
        return {
            "MenuText": "Split Member",
            "ToolTip": (
                "Split one selected ForgeCAD straight member "
                "at a point on its centerline"
            ),
        }

    def Activated(
        self,
    ):
        global _active_tool

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

        selection = list(
            FreeCADGui.Selection.getSelection()
        )

        if len(
            selection
        ) != 1:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select One Member",
                (
                    "Select exactly one ForgeCAD straight "
                    "member, then run Split Member."
                ),
            )
            return

        member_object = (
            selection[
                0
            ]
        )

        if not is_forgecad_member(
            member_object
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Selection",
                (
                    "Split Member requires one "
                    "ForgeCAD straight member."
                ),
            )
            return

        if _active_tool is not None:
            _active_tool.stop()

        _active_tool = (
            InteractiveSplitMemberTool(
                document,
                member_object,
            )
        )

        FreeCADGui.Selection.clearSelection()

        _active_tool.start()

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Split Member command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        SplitMemberCommand(),
    )
