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

_active_tool = None


class InteractiveLayoutLineTool:
    """Create ForgeCAD layout lines using viewport clicks."""

    def __init__(self):
        self.view = None
        self.mouse_callback = None
        self.move_callback = None

        self.start_point = None

        self.preview_line = None
        self.start_marker = None
        self.snap_marker = None

    def start(self):
        """Begin listening for viewport mouse events."""

        self.view = FreeCADGui.activeDocument().activeView()

        self.mouse_callback = self.view.addEventCallback(
            "SoMouseButtonEvent",
            self.on_mouse_event,
        )

        self.move_callback = self.view.addEventCallback(
            "SoLocation2Event",
            self.on_mouse_move,
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

        self.mouse_callback = None
        self.move_callback = None

        self.remove_preview()

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
        """Find the nearest layout endpoint within snap tolerance."""

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

    def resolved_point(self, position):
        """Return snapped endpoint or free-space cursor point."""

        snap_point = self.find_snap_point(position)

        if snap_point is not None:
            return snap_point, True

        return self.screen_to_point(position), False

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

    def on_mouse_move(self, event):
        """Update snapping and preview while the cursor moves."""

        position = event.get("Position")

        if position is None:
            return

        snap_point = self.find_snap_point(position)

        self.update_snap_marker(snap_point)

        if self.start_point is None:
            return

        point, _ = self.resolved_point(position)

        if point is None:
            return

        self.update_preview_line(
            self.start_point,
            point,
        )

    def on_mouse_event(self, event):
        """Handle viewport mouse-button events."""

        if event.get("Button") != "BUTTON1":
            return

        if event.get("State") != "DOWN":
            return

        position = event.get("Position")

        point, _ = self.resolved_point(position)

        if point is None:
            return

        if self.start_point is None:
            self.start_point = point

            self.create_start_marker(point)

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

        self.start_point = None

        self.stop()

        FreeCADGui.activeDocument().activeView().fitAll()


class DrawLayoutLineInteractiveCommand:
    """Start interactive two-click layout-line creation."""

    def GetResources(self):
        return {
            "MenuText": "Draw Layout Line Interactively",
            "ToolTip": (
                "Create a ForgeCAD layout line by clicking "
                "two points in the viewport with endpoint snapping"
            ),
        }

    def Activated(self):
        global _active_tool

        document = FreeCAD.ActiveDocument

        if document is None:
            document = FreeCAD.newDocument("ForgeCAD_Layout")

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
    