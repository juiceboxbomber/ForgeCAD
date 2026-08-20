"""Interactive FreeCAD command for creating ForgeCAD layout lines."""

import math

import FreeCAD
import FreeCADGui
import Part
from PySide import QtCore, QtGui

from forgecad import LayoutLine
from forgecad.geometry import Point3D
from forgecad.services.grid_snap import (
    snap_xy_coordinates,
)
from forgecad.adapters.freecad.commands.draw_layout_line import (
    create_layout_line_object,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


COMMAND_NAME = "ForgeCAD_DrawLayoutLineInteractive"

SNAP_DISTANCE_PIXELS = 15
ANGLE_INCREMENT_DEGREES = 15.0
ANGLE_SNAP_TOLERANCE_DEGREES = 3.0
LAYOUT_PLANE_Z = 0.0

_active_tool = None


class LengthInput(QtGui.QLineEdit):
    """Length-entry box used by the interactive layout tool."""

    def __init__(self, tool):
        super().__init__()

        self.tool = tool

        self.setPlaceholderText("Length")
        self.setFixedWidth(100)

    def keyPressEvent(self, event):
        """Allow Escape to finish the drawing tool."""

        if event.key() == QtCore.Qt.Key_Escape:
            self.tool.stop()
            return

        super().keyPressEvent(event)


class InteractiveLayoutLineTool:
    """Create ForgeCAD layout lines interactively."""

    def __init__(self):
        self.view = None

        self.mouse_callback = None
        self.move_callback = None
        self.keyboard_callback = None

        self.start_point = None
        self.last_resolved_point = None

        self.preview_line = None
        self.start_marker = None
        self.snap_marker = None

        self.status_bar = None

        self.length_label = None
        self.length_input = None

        self.cached_layout_segments = ()
        self.cached_layout_endpoints = ()

    def start(self):
        """Start the interactive drawing tool."""

        self.view = FreeCADGui.activeDocument().activeView()

        self.status_bar = FreeCADGui.getMainWindow().statusBar()

        self.create_length_input()
        self.refresh_snap_cache()

        self.mouse_callback = self.view.addEventCallback(
            "SoMouseButtonEvent",
            self.on_mouse_event,
        )

        self.move_callback = self.view.addEventCallback(
            "SoLocation2Event",
            self.on_mouse_move,
        )

        self.keyboard_callback = self.view.addEventCallback(
            "SoKeyboardEvent",
            self.on_keyboard_event,
        )

        self.show_status(
            "ForgeCAD: Click first point. "
            "Grid, endpoint, and line snapping active. "
            "Esc: Finish."
        )

    def create_length_input(self):
        """Create the exact-length input in the status bar."""

        self.length_label = QtGui.QLabel("  Length (mm):")

        self.length_input = LengthInput(self)

        validator = QtGui.QDoubleValidator(
            0.001,
            1000000.0,
            3,
            self.length_input,
        )

        self.length_input.setValidator(validator)

        self.length_input.returnPressed.connect(
            self.accept_numeric_length
        )

        self.length_input.setEnabled(False)

        self.status_bar.addPermanentWidget(
            self.length_label
        )

        self.status_bar.addPermanentWidget(
            self.length_input
        )

    def remove_length_input(self):
        """Remove the status-bar length control."""

        if self.status_bar is None:
            return

        if self.length_label is not None:
            self.status_bar.removeWidget(
                self.length_label
            )

            self.length_label.deleteLater()
            self.length_label = None

        if self.length_input is not None:
            self.status_bar.removeWidget(
                self.length_input
            )

            self.length_input.deleteLater()
            self.length_input = None

    def enable_length_input(self):
        """Enable exact-length entry after a start point exists."""

        if self.length_input is None:
            return

        self.length_input.setEnabled(True)
        self.length_input.clear()
        self.length_input.setFocus()
        self.length_input.selectAll()

    def clear_length_input(self):
        """Clear length entry while keeping it ready for another segment."""

        if self.length_input is None:
            return

        self.length_input.clear()

    def show_status(self, message):
        """Show information in the FreeCAD status bar."""

        if self.status_bar is not None:
            self.status_bar.showMessage(message)

    def _remove_view_callback(
        self,
        event_name,
        callback,
    ):
        """Safely remove one viewport callback if the view still exists."""

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
            # FreeCAD may already have destroyed the underlying
            # Quarter/Coin view object during workbench or document
            # changes. Cleanup must remain idempotent in that case.
            pass

    def stop(self):
        """Stop drawing and clean up temporary objects."""

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

        self.start_point = None
        self.last_resolved_point = None

        self.remove_preview()
        self.remove_length_input()

        if self.status_bar is not None:
            try:
                self.status_bar.clearMessage()
            except Exception:
                pass

        self.status_bar = None
        self.view = None

    def remove_object(self, obj):
        """Safely remove a temporary FreeCAD object."""

        if obj is None:
            return

        document = FreeCAD.ActiveDocument

        if document is None:
            return

        try:
            document.removeObject(obj.Name)
        except Exception:
            pass

    def remove_preview(self):
        """Remove all temporary drawing geometry."""

        document = FreeCAD.ActiveDocument

        if document is None:
            return

        self.remove_object(self.preview_line)
        self.remove_object(self.start_marker)
        self.remove_object(self.snap_marker)

        self.preview_line = None
        self.start_marker = None
        self.snap_marker = None

        document.recompute()

    def screen_to_point(self, position):
        """
        Convert screen position to the ForgeCAD XY layout plane.

        FreeCAD's viewport projection may return small Z offsets
        depending on camera state or visible geometry. Layout-line
        creation is intentionally constrained to Z=0.
        """

        if position is None:
            return None

        point = self.view.getPoint(
            int(position[0]),
            int(position[1]),
        )

        return Point3D(
            float(point.x),
            float(point.y),
            LAYOUT_PLANE_Z,
        )

    def workspace_minor_grid_spacing(self):
        """Return the active project's stored minor-grid spacing."""

        document = FreeCAD.ActiveDocument

        if document is None:
            return None

        workspace = document.getObject(
            "ForgeCADWorkspace"
        )

        if workspace is None:
            return None

        if (
            hasattr(
                workspace,
                "SnapEnabled",
            )
            and not bool(
                workspace.SnapEnabled
            )
        ):
            return None

        if not hasattr(
            workspace,
            "MinorGridSpacing",
        ):
            return None

        try:
            spacing = float(
                workspace.MinorGridSpacing
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        if spacing <= 0.0:
            return None

        return spacing

    def snap_point_to_grid(
        self,
        point,
    ):
        """Snap a free XY point to the active project's minor grid."""

        if point is None:
            return None

        spacing = (
            self.workspace_minor_grid_spacing()
        )

        if spacing is None:
            return None

        snapped_x, snapped_y = (
            snap_xy_coordinates(
                point.x,
                point.y,
                spacing,
            )
        )

        return Point3D(
            snapped_x,
            snapped_y,
            LAYOUT_PLANE_Z,
        )

    def refresh_snap_cache(self):
        """Cache layout geometry used by interactive snapping."""

        document = FreeCAD.ActiveDocument

        if document is None:
            self.cached_layout_segments = ()
            self.cached_layout_endpoints = ()
            return

        segments = []

        for obj in document.Objects:
            if not hasattr(obj, "StartPoint"):
                continue

            if not hasattr(obj, "EndPoint"):
                continue

            start = obj.StartPoint
            end = obj.EndPoint

            start_point = Point3D(
                float(start.x),
                float(start.y),
                float(start.z),
            )

            end_point = Point3D(
                float(end.x),
                float(end.y),
                float(end.z),
            )

            if start_point == end_point:
                continue

            segments.append(
                (
                    start_point,
                    end_point,
                )
            )

        self.cached_layout_segments = tuple(
            segments
        )

        self.cached_layout_endpoints = tuple(
            point
            for segment in self.cached_layout_segments
            for point in segment
        )

    def layout_segments(self):
        """Return cached existing ForgeCAD line segments."""

        return list(
            self.cached_layout_segments
        )

    def layout_endpoints(self):
        """Return cached existing ForgeCAD layout endpoints."""

        return list(
            self.cached_layout_endpoints
        )

    def point_to_screen(self, point):
        """Convert a ForgeCAD point to screen coordinates."""

        vector = FreeCAD.Vector(
            point.x,
            point.y,
            point.z,
        )

        screen = self.view.getPointOnScreen(
            vector
        )

        return (
            float(screen[0]),
            float(screen[1]),
        )

    def find_snap_point(self, position):
        """Find nearest endpoint within snap tolerance."""

        if position is None:
            return None

        mouse_x = float(position[0])
        mouse_y = float(position[1])

        nearest_point = None
        nearest_distance = SNAP_DISTANCE_PIXELS

        for endpoint in self.layout_endpoints():
            try:
                screen_x, screen_y = (
                    self.point_to_screen(endpoint)
                )
            except Exception:
                continue

            distance = math.hypot(
                screen_x - mouse_x,
                screen_y - mouse_y,
            )

            if distance <= nearest_distance:
                nearest_distance = distance
                nearest_point = endpoint

        return nearest_point

    def point_on_screen_segment(
        self,
        position,
        start,
        end,
    ):
        """
        Return the exact 3D point on a segment nearest the mouse.

        The nearest location is chosen in screen space so snapping
        feels natural in the active view. The returned point is then
        interpolated on the original 3D segment, so the committed
        geometry lies exactly on the existing centerline.
        """

        if position is None:
            return None, None

        try:
            start_x, start_y = (
                self.point_to_screen(
                    start
                )
            )

            end_x, end_y = (
                self.point_to_screen(
                    end
                )
            )

        except Exception:
            return None, None

        mouse_x = float(
            position[0]
        )

        mouse_y = float(
            position[1]
        )

        segment_x = (
            end_x - start_x
        )

        segment_y = (
            end_y - start_y
        )

        screen_length_squared = (
            segment_x * segment_x
            + segment_y * segment_y
        )

        if screen_length_squared <= 1e-12:
            return None, None

        parameter = (
            (
                (mouse_x - start_x)
                * segment_x
                + (mouse_y - start_y)
                * segment_y
            )
            / screen_length_squared
        )

        parameter = max(
            0.0,
            min(
                1.0,
                parameter,
            ),
        )

        snap_screen_x = (
            start_x
            + parameter * segment_x
        )

        snap_screen_y = (
            start_y
            + parameter * segment_y
        )

        screen_distance = math.hypot(
            snap_screen_x - mouse_x,
            snap_screen_y - mouse_y,
        )

        point = Point3D(
            start.x
            + parameter
            * (
                end.x - start.x
            ),
            start.y
            + parameter
            * (
                end.y - start.y
            ),
            start.z
            + parameter
            * (
                end.z - start.z
            ),
        )

        return point, screen_distance

    def find_line_snap_point(
        self,
        position,
    ):
        """Find the nearest exact point on an existing line segment."""

        if position is None:
            return None

        nearest_point = None
        nearest_distance = (
            SNAP_DISTANCE_PIXELS
        )

        for start, end in self.layout_segments():
            point, distance = (
                self.point_on_screen_segment(
                    position,
                    start,
                    end,
                )
            )

            if (
                point is None
                or distance is None
            ):
                continue

            if distance <= nearest_distance:
                nearest_distance = distance
                nearest_point = point

        return nearest_point

    def infer_angle(self, point):
        """Apply XY-plane angle inference."""

        if self.start_point is None:
            return point, None

        dx = point.x - self.start_point.x
        dy = point.y - self.start_point.y

        length_xy = math.hypot(
            dx,
            dy,
        )

        if length_xy <= 0.000001:
            return point, None

        angle = math.degrees(
            math.atan2(
                dy,
                dx,
            )
        )

        normalized_angle = angle % 360.0

        snapped_angle = round(
            normalized_angle
            / ANGLE_INCREMENT_DEGREES
        ) * ANGLE_INCREMENT_DEGREES

        snapped_angle %= 360.0

        difference = abs(
            (
                normalized_angle
                - snapped_angle
                + 180.0
            )
            % 360.0
            - 180.0
        )

        if (
            difference
            > ANGLE_SNAP_TOLERANCE_DEGREES
        ):
            return point, None

        radians = math.radians(
            snapped_angle
        )

        snapped_point = Point3D(
            self.start_point.x
            + length_xy * math.cos(radians),
            self.start_point.y
            + length_xy * math.sin(radians),
            point.z,
        )

        return snapped_point, snapped_angle

    def resolved_point(self, position):
        """
        Resolve endpoint snap, line snap, grid snap, angle inference,
        or free position.

        Snap priority is:

            endpoint
            existing line
            project grid
            angle inference
            free position
        """

        snap_point = self.find_snap_point(
            position
        )

        if snap_point is not None:
            return (
                snap_point,
                "ENDPOINT",
                None,
            )

        line_snap_point = (
            self.find_line_snap_point(
                position
            )
        )

        if line_snap_point is not None:
            return (
                line_snap_point,
                "LINE",
                None,
            )

        free_point = self.screen_to_point(
            position
        )

        if free_point is None:
            return None, None, None

        grid_point = self.snap_point_to_grid(
            free_point
        )

        candidate_point = (
            grid_point
            if grid_point is not None
            else free_point
        )

        if self.start_point is None:
            if grid_point is not None:
                return (
                    grid_point,
                    "GRID",
                    None,
                )

            return (
                free_point,
                None,
                None,
            )

        inferred_point, snapped_angle = (
            self.infer_angle(
                candidate_point
            )
        )

        if snapped_angle is not None:
            return (
                inferred_point,
                "ANGLE",
                snapped_angle,
            )

        if grid_point is not None:
            return (
                grid_point,
                "GRID",
                None,
            )

        return (
            free_point,
            None,
            None,
        )

    def create_start_marker(self, point):
        """Show the current segment start point."""

        document = FreeCAD.ActiveDocument

        if document is None:
            return

        marker = document.addObject(
            "Part::Feature",
            "ForgeCADTemporaryStartPoint",
        )

        marker.Label = "Layout Start Point"

        marker.Shape = Part.makeSphere(
            8.0,
            FreeCAD.Vector(
                point.x,
                point.y,
                point.z,
            ),
        )

        self.start_marker = marker

        document.recompute()

    def update_snap_marker(self, point):
        """Show or remove the active snap marker."""

        document = FreeCAD.ActiveDocument

        if document is None:
            return

        if point is None:
            if self.snap_marker is not None:
                self.remove_object(
                    self.snap_marker
                )

                self.snap_marker = None

            return

        if self.snap_marker is None:
            self.snap_marker = (
                document.addObject(
                    "Part::Feature",
                    "ForgeCADTemporarySnapPoint",
                )
            )

            self.snap_marker.Label = (
                "Geometry Snap"
            )

        self.snap_marker.Shape = (
            Part.makeSphere(
                12.0,
                FreeCAD.Vector(
                    point.x,
                    point.y,
                    point.z,
                ),
            )
        )

    def update_preview_line(
        self,
        start,
        end,
    ):
        """Update temporary preview geometry."""

        if start == end:
            return

        document = FreeCAD.ActiveDocument

        if document is None:
            return

        start_vector = FreeCAD.Vector(
            start.x,
            start.y,
            start.z,
        )

        end_vector = FreeCAD.Vector(
            end.x,
            end.y,
            end.z,
        )

        if self.preview_line is None:
            self.preview_line = (
                document.addObject(
                    "Part::Feature",
                    "ForgeCADTemporaryLayoutLine",
                )
            )

            self.preview_line.Label = (
                "Layout Line Preview"
            )

        self.preview_line.Shape = (
            Part.makeLine(
                start_vector,
                end_vector,
            )
        )

    def line_measurements(
        self,
        start,
        end,
    ):
        """Return line length and XY angle."""

        dx = end.x - start.x
        dy = end.y - start.y
        dz = end.z - start.z

        length = math.sqrt(
            dx * dx
            + dy * dy
            + dz * dz
        )

        angle = math.degrees(
            math.atan2(
                dy,
                dx,
            )
        )

        angle %= 360.0

        return length, angle

    def inference_name(
        self,
        snap_type,
        snapped_angle,
    ):
        """Return readable inference name."""

        if snap_type == "ENDPOINT":
            return "ENDPOINT"

        if snap_type == "LINE":
            return "ON LINE"

        if snap_type == "GRID":
            return "GRID"

        if snap_type != "ANGLE":
            return ""

        if snapped_angle is None:
            return ""

        angle = snapped_angle % 360.0

        if angle in (0.0, 180.0):
            return "HORIZONTAL"

        if angle in (90.0, 270.0):
            return "VERTICAL"

        return (
            f"ANGLE SNAP "
            f"{angle:.0f} deg"
        )

    def update_measurement_display(
        self,
        point,
        snap_type,
        snapped_angle,
    ):
        """Display live length and angle."""

        if self.start_point is None:
            return

        length, angle = (
            self.line_measurements(
                self.start_point,
                point,
            )
        )

        inference = self.inference_name(
            snap_type,
            snapped_angle,
        )

        message = (
            f"ForgeCAD | "
            f"Length: {length:.2f} mm | "
            f"Angle: {angle:.2f} deg"
        )

        if inference:
            message += (
                f" | {inference}"
            )

        message += (
            " | Enter exact length at right"
            " | Esc: Finish"
        )

        self.show_status(
            message
        )

    def point_at_length(
        self,
        length,
    ):
        """Create a point at exact length along current preview direction."""

        if self.start_point is None:
            return None

        if self.last_resolved_point is None:
            return None

        dx = (
            self.last_resolved_point.x
            - self.start_point.x
        )

        dy = (
            self.last_resolved_point.y
            - self.start_point.y
        )

        dz = (
            self.last_resolved_point.z
            - self.start_point.z
        )

        magnitude = math.sqrt(
            dx * dx
            + dy * dy
            + dz * dz
        )

        if magnitude <= 0.000001:
            return None

        scale = length / magnitude

        return Point3D(
            self.start_point.x
            + dx * scale,
            self.start_point.y
            + dy * scale,
            self.start_point.z
            + dz * scale,
        )

    def commit_line(
        self,
        point,
    ):
        """Create a layout line and continue from its endpoint."""

        if self.start_point is None:
            return

        try:
            layout_line = LayoutLine(
                start=self.start_point,
                end=point,
            )
        except ValueError:
            return

        document = FreeCAD.ActiveDocument

        if document is None:
            self.stop()
            return

        groups = initialize_project_tree(
            document
        )

        layout_object = (
            create_layout_line_object(
                document,
                layout_line,
            )
        )

        groups["Layout"].addObject(
            layout_object
        )

        document.recompute()
        self.refresh_snap_cache()

        self.start_point = point
        self.last_resolved_point = None

        self.remove_object(
            self.start_marker
        )

        self.start_marker = None

        self.create_start_marker(
            self.start_point
        )

        self.remove_object(
            self.preview_line
        )

        self.preview_line = None

        self.update_snap_marker(
            None
        )

        self.clear_length_input()

        self.show_status(
            "ForgeCAD: Continue drawing. "
            "Move cursor to choose direction. "
            "Enter exact length if needed. "
            "Esc: Finish."
        )



    def accept_numeric_length(self):
        """Commit an exact line length from the length box."""

        if self.start_point is None:
            return

        if self.length_input is None:
            return

        text = (
            self.length_input.text()
            .strip()
        )

        if not text:
            return

        try:
            length = float(text)
        except ValueError:
            return

        if length <= 0:
            return

        point = self.point_at_length(
            length
        )

        if point is None:
            self.show_status(
                "ForgeCAD: Move the mouse first "
                "to establish the line direction."
            )
            return

        self.commit_line(
            point
        )

        self.enable_length_input()

    def on_mouse_move(self, event):
        """Update snapping, preview, and measurements."""

        position = event.get(
            "Position"
        )

        if position is None:
            return

        point, snap_type, snapped_angle = (
            self.resolved_point(
                position
            )
        )

        if point is None:
            return

        self.last_resolved_point = point

        if snap_type in (
            "ENDPOINT",
            "LINE",
            "GRID",
        ):
            self.update_snap_marker(
                point
            )
        else:
            self.update_snap_marker(
                None
            )

        if self.start_point is None:
            return

        self.update_preview_line(
            self.start_point,
            point,
        )

        self.update_measurement_display(
            point,
            snap_type,
            snapped_angle,
        )

    def on_keyboard_event(self, event):
        """Handle Escape when viewport has focus."""

        if event.get("State") != "DOWN":
            return

        key = event.get("Key")

        if key in (
            "ESCAPE",
            "ESC",
        ):
            self.stop()

    def on_mouse_event(self, event):
        """Handle left mouse clicks."""

        button = event.get(
            "Button"
        )

        state = event.get(
            "State"
        )

        if state != "DOWN":
            return

        if button != "BUTTON1":
            return

        position = event.get(
            "Position"
        )

        point, _, _ = (
            self.resolved_point(
                position
            )
        )

        if point is None:
            return

        self.last_resolved_point = point

        if self.start_point is None:
            self.start_point = point

            self.create_start_marker(
                point
            )

            self.enable_length_input()

            self.show_status(
                "ForgeCAD: Move cursor to choose "
                "direction. Enter exact length "
                "in the Length box. Esc: Finish."
            )

            return

        self.commit_line(
            point
        )

        self.enable_length_input()


class DrawLayoutLineInteractiveCommand:
    """Start interactive continuous layout-line creation."""

    def GetResources(self):
        return {
            "MenuText":
                "Draw Layout Line Interactively",
            "ToolTip": (
                "Draw continuous ForgeCAD layout "
                "lines with snapping, angle inference, "
                "and exact length input"
            ),
        }

    def Activated(self):
        global _active_tool

        document = (
            FreeCAD.ActiveDocument
        )

        if document is None:
            document = FreeCAD.newDocument(
                "ForgeCAD_Layout"
            )

        if _active_tool is not None:
            _active_tool.stop()

        _active_tool = (
            InteractiveLayoutLineTool()
        )

        _active_tool.start()

    def IsActive(self):
        return True


def register_command() -> None:
    """Register the interactive layout-line command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        DrawLayoutLineInteractiveCommand(),
    )
