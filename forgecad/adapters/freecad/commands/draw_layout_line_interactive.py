"""Interactive FreeCAD command for creating ForgeCAD layout lines."""

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

_active_tool = None


class InteractiveLayoutLineTool:
    """Create a ForgeCAD layout line using two viewport clicks."""

    def __init__(self):
        self.view = None
        self.mouse_callback = None
        self.move_callback = None

        self.start_point = None

        self.preview_line = None
        self.start_marker = None

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
        """Stop listening and remove temporary preview geometry."""

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

    def remove_preview(self):
        """Remove temporary preview objects from the document."""

        document = FreeCAD.ActiveDocument

        if document is None:
            return

        if self.preview_line is not None:
            try:
                document.removeObject(self.preview_line.Name)
            except Exception:
                pass

            self.preview_line = None

        if self.start_marker is not None:
            try:
                document.removeObject(self.start_marker.Name)
            except Exception:
                pass

            self.start_marker = None

        document.recompute()

    def screen_to_point(self, position):
        """Convert a viewport position into a ForgeCAD point."""

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

    def create_start_marker(self, point: Point3D):
        """Create a temporary marker at the first selected point."""

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

    def update_preview_line(
        self,
        start: Point3D,
        end: Point3D,
    ):
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
            preview = document.addObject(
                "Part::Feature",
                "ForgeCADTemporaryLayoutLine",
            )

            preview.Label = "Layout Line Preview"
            self.preview_line = preview

        self.preview_line.Shape = Part.makeLine(
            start_vector,
            end_vector,
        )

        document.recompute()

    def on_mouse_move(self, event):
        """Update the preview line while the mouse moves."""

        if self.start_point is None:
            return

        position = event.get("Position")

        current_point = self.screen_to_point(position)

        if current_point is None:
            return

        self.update_preview_line(
            self.start_point,
            current_point,
        )

    def on_mouse_event(self, event):
        """Handle viewport mouse-button events."""

        if event.get("Button") != "BUTTON1":
            return

        if event.get("State") != "DOWN":
            return

        position = event.get("Position")

        point = self.screen_to_point(position)

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
                "Create a ForgeCAD layout line "
                "by clicking two points in the viewport"
            ),
        }

    def Activated(self):
        global _active_tool

        document = FreeCAD.ActiveDocument

        if document is None:
            document = FreeCAD.newDocument("ForgeCAD_Layout")

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
    