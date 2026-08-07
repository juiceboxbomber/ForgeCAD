"""Interactive FreeCAD command for creating ForgeCAD layout lines."""

import math

import FreeCAD
import FreeCADGui
import Part

from forgecad import LayoutLine
from forgecad.geometry import Point3D
from forgecad.adapters.freecad.commands.draw_layout_line import (
    create_layout_line_object,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)


COMMAND_NAME = "ForgeCAD_DrawLayoutLineInteractive"

SNAP_DISTANCE_PIXELS = 15

# Angle inference settings.
ANGLE_INCREMENT_DEGREES = 15.0
ANGLE_SNAP_TOLERANCE_DEGREES = 3.0

_active_tool = None


class InteractiveLayoutLineTool:
    """Create ForgeCAD layout lines using viewport clicks."""

    def __init__(self):
        self.view = None
        self.mouse_callback = None
        self.move_callback = None
        self.keyboard_callback = None

        self.start_point = None

        self.preview_line = None
        self.start_marker = None
        self.snap_marker = None

        self.status_bar = None

    def start(self):
        """Begin listening for viewport mouse and keyboard events."""

        self.view = FreeCADGui.activeDocument().activeView()
        self.status_bar = FreeCADGui.getMainWindow().statusBar()

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
            "ForgeCAD: Click first point. Press Esc to finish."
        )

    def stop(self):
        """Stop listening and remove temporary geometry."""

        if self.view is not None:
            if self.mouse_callback is not None:
                self.view.removeEventCallback(
                    "SoMouseButtonEvent",
                    self.mouse_callback,
                )

            if self.move_callback is not None:
                self.view.removeEventCallback(
                    "SoLocation2Event",
                    self.move_callback,
                )

            if self.keyboard_callback is not None:
                self.view.removeEventCallback(
                    "SoKeyboardEvent",
                    self.keyboard_callback,
                )

        self.mouse_callback = None
        self.move_callback = None
        self.keyboard_callback = None

        self.start_point = None

        self.remove_preview()

        if self.status_bar is not None:
            self.status_bar.clearMessage()

        self.status_bar = None
        self.view = None

    def show_status(self, message):
        """Show drawing information in the FreeCAD status bar."""

        if self.status_bar is not None:
            self.status_bar.showMessage(message)

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
        """Remove all temporary drawing objects."""

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
        """Convert viewport coordinates to a ForgeCAD point."""

        if position is None:
            return None

        point = self.view.getPoint(
            int(position[0]),
            int(position[1]),
        )

        return Point3D(
            float(point.x),
            float(point.y),
            float(point.z),
        )

    def layout_endpoints(self):
        """Return endpoints from existing ForgeCAD layout lines."""

        document = FreeCAD.ActiveDocument

        if document is None:
            return []

        endpoints = []

        for obj in document.Objects:
            if not hasattr(obj, "StartPoint"):
                continue

            if not hasattr(obj, "EndPoint"):
                continue

            start = obj.StartPoint
            end = obj.EndPoint

            endpoints.append(
                Point3D(
                    float(start.x),
                    float(start.y),
                    float(start.z),
                )
            )

            endpoints.append(
                Point3D(
                    float(end.x),
                    float(end.y),
                    float(end.z),
                )
            )

        return endpoints

    def point_to_screen(self, point):
        """Convert a ForgeCAD point to viewport screen coordinates."""

        vector = FreeCAD.Vector(
            point.x,
            point.y,
            point.z,
        )

        screen = self.view.getPointOnScreen(vector)

        return float(screen[0]), float(screen[1])

    def find_snap_point(self, position):
        """Find nearest existing layout endpoint within snap tolerance."""

        if position is None:
            return None

        mouse_x = float(position[0])
        mouse_y = float(position[1])

        nearest_point = None
        nearest_distance = SNAP_DISTANCE_PIXELS

        for endpoint in self.layout_endpoints():
            try:
                screen_x, screen_y = self.point_to_screen(endpoint)
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

    def infer_angle(self, point):
        """
        Apply angle inference from the current start point.

        This first version works in the XY drawing plane and snaps to
        multiples of 15 degrees when within the angular tolerance.
        """

        if self.start_point is None:
            return point, None

        dx = point.x - self.start_point.x
        dy = point.y - self.start_point.y

        length_xy = math.hypot(dx, dy)

        if length_xy <= 0.000001:
            return point, None

        angle = math.degrees(
            math.atan2(dy, dx)
        )

        normalized_angle = angle % 360.0

        snapped_angle = round(
            normalized_angle / ANGLE_INCREMENT_DEGREES
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

        if difference > ANGLE_SNAP_TOLERANCE_DEGREES:
            return point, None

        radians = math.radians(snapped_angle)

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
        Resolve the cursor using snap priority.

        Existing endpoint snapping has priority over angle inference.
        """

        snap_point = self.find_snap_point(position)

        if snap_point is not None:
            return snap_point, "ENDPOINT", None

        free_point = self.screen_to_point(position)

        if free_point is None:
            return None, None, None

        if self.start_point is None:
            return free_point, None, None

        inferred_point, snapped_angle = self.infer_angle(
            free_point
        )

        if snapped_angle is not None:
            return inferred_point, "ANGLE", snapped_angle

        return free_point, None, None

    def create_start_marker(self, point):
        """Show the selected first point."""

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
        """Show or move the endpoint snap marker."""

        document = FreeCAD.ActiveDocument

        if document is None:
            return

        if point is None:
            if self.snap_marker is not None:
                self.remove_object(self.snap_marker)
                self.snap_marker = None
                document.recompute()

            return

        if self.snap_marker is None:
            self.snap_marker = document.addObject(
                "Part::Feature",
                "ForgeCADTemporarySnapPoint",
            )

            self.snap_marker.Label = "Endpoint Snap"

        self.snap_marker.Shape = Part.makeSphere(
            12.0,
            FreeCAD.Vector(
                point.x,
                point.y,
                point.z,
            ),
        )

        document.recompute()

    def update_preview_line(self, start, end):
        """Update the temporary line shown under the cursor."""

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
            self.preview_line = document.addObject(
                "Part::Feature",
                "ForgeCADTemporaryLayoutLine",
            )

            self.preview_line.Label = "Layout Line Preview"

        self.preview_line.Shape = Part.makeLine(
            start_vector,
            end_vector,
        )

        document.recompute()

    def line_measurements(self, start, end):
        """Return 3D length and XY-plane angle."""

        dx = end.x - start.x
        dy = end.y - start.y
        dz = end.z - start.z

        length = math.sqrt(
            dx * dx
            + dy * dy
            + dz * dz
        )

        angle = math.degrees(
            math.atan2(dy, dx)
        )

        angle %= 360.0

        return length, angle

    def inference_name(self, snap_type, snapped_angle):
        """Return readable text describing the active inference."""

        if snap_type == "ENDPOINT":
            return "ENDPOINT"

        if snap_type != "ANGLE":
            return ""

        if snapped_angle is None:
            return ""

        angle = snapped_angle % 360.0

        if angle in (0.0, 180.0):
            return "HORIZONTAL"

        if angle in (90.0, 270.0):
            return "VERTICAL"

        return f"ANGLE SNAP {angle:.0f} deg"

    def update_measurement_display(
        self,
        point,
        snap_type,
        snapped_angle,
    ):
        """Display live length, angle, and inference information."""

        if self.start_point is None:
            self.show_status(
                "ForgeCAD: Click first point. Press Esc to finish."
            )
            return

        length, angle = self.line_measurements(
            self.start_point,
            point,
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
            message += f" | {inference}"

        message += " | Esc: Finish"

        self.show_status(message)

    def on_mouse_move(self, event):
        """Update snapping, inference, preview, and measurements."""

        position = event.get("Position")

        if position is None:
            return

        point, snap_type, snapped_angle = self.resolved_point(
            position
        )

        if point is None:
            return

        if snap_type == "ENDPOINT":
            self.update_snap_marker(point)
        else:
            self.update_snap_marker(None)

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
        """Finish interactive drawing when Escape is pressed."""

        if event.get("State") != "DOWN":
            return

        key = event.get("Key")

        if key not in ("ESCAPE", "ESC"):
            return

        self.stop()

    def on_mouse_event(self, event):
        """Handle viewport mouse-button events."""

        button = event.get("Button")
        state = event.get("State")

        if state != "DOWN":
            return

        if button != "BUTTON1":
            return

        position = event.get("Position")

        point, _, _ = self.resolved_point(position)

        if point is None:
            return

        if self.start_point is None:
            self.start_point = point

            self.create_start_marker(point)

            self.show_status(
                "ForgeCAD: Move cursor for length/angle. "
                "Click next point. Esc: Finish."
            )

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

        groups = initialize_project_tree(document)

        layout_object = create_layout_line_object(
            document,
            layout_line,
        )

        groups["Layout"].addObject(layout_object)

        document.recompute()

        # Continuous drawing:
        # the endpoint becomes the start of the next line.
        self.start_point = point

        self.remove_object(self.start_marker)
        self.start_marker = None

        self.create_start_marker(
            self.start_point
        )

        self.remove_object(self.preview_line)
        self.preview_line = None

        self.update_snap_marker(None)

        self.show_status(
            "ForgeCAD: Continue drawing. Esc: Finish."
        )

        document.recompute()


class DrawLayoutLineInteractiveCommand:
    """Start interactive continuous layout-line creation."""

    def GetResources(self):
        return {
            "MenuText": "Draw Layout Line Interactively",
            "ToolTip": (
                "Draw continuous ForgeCAD layout lines with "
                "endpoint and angle snapping"
            ),
        }

    def Activated(self):
        global _active_tool

        document = FreeCAD.ActiveDocument

        if document is None:
            document = FreeCAD.newDocument(
                "ForgeCAD_Layout"
            )

        if _active_tool is not None:
            _active_tool.stop()

        _active_tool = InteractiveLayoutLineTool()
        _active_tool.start()

    def IsActive(self):
        return True


def register_command() -> None:
    """Register the interactive layout-line command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        DrawLayoutLineInteractiveCommand(),
    )
    