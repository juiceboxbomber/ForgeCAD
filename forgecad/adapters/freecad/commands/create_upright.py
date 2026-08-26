"""Interactive FreeCAD command for creating a vertical ForgeCAD upright."""

import math

import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui

from forgecad.geometry import Point3D
from forgecad.adapters.freecad.commands.create_member_between_nodes import (
    create_member_between_nodes,
)
from forgecad.adapters.freecad.commands.draw_member_interactive import (
    get_or_create_node,
)
from forgecad.adapters.freecad.commands.split_member import (
    SNAP_DISTANCE_PIXELS,
    is_forgecad_member,
    member_centerline,
    screen_point_on_segment,
)
from forgecad.adapters.freecad.fabrication_refresh import (
    refresh_fabrication_for_document,
)
from forgecad.adapters.freecad.topology_refresh import (
    refresh_joint_topology,
)


COMMAND_NAME = "ForgeCAD_CreateUpright"
PREVIEW_OBJECT_NAME = "ForgeCADUprightPreview"

_active_tool = None


def upright_end_point(
    start_point,
    height,
):
    """Return the global +Z endpoint for an upright."""

    height = float(
        height
    )

    if height <= 0.0:
        raise ValueError(
            "Upright height must be greater than zero."
        )

    return Point3D(
        float(
            start_point.x
        ),
        float(
            start_point.y
        ),
        float(
            start_point.z
        )
        + height,
    )


def create_upright(
    document,
    start_point,
    height,
):
    """
    Create one vertical ForgeCAD member from a point on existing geometry.

    The source member is not split. A persistent node is created or reused
    at the picked centerline point, another is created/reused directly above
    it, and a normal ForgeCAD member is created between those nodes.
    """

    if document is None:
        raise ValueError(
            "A FreeCAD document is required."
        )

    end_point = upright_end_point(
        start_point,
        height,
    )

    start_node = get_or_create_node(
        document,
        start_point,
    )

    end_node = get_or_create_node(
        document,
        end_point,
    )

    (
        layout_object,
        member_object,
    ) = create_member_between_nodes(
        document,
        start_node,
        end_node,
        refresh=False,
    )

    document.recompute()

    refresh_joint_topology(
        document
    )

    refresh_fabrication_for_document(
        document
    )

    document.recompute()

    return (
        layout_object,
        member_object,
        start_node,
        end_node,
    )


def quantity_value(
    value,
):
    """Return a numeric value from a FreeCAD quantity or test double."""

    return float(
        getattr(
            value,
            "Value",
            value,
        )
    )


def member_length(
    start,
    end,
):
    """Return the 3D centerline length between two points."""

    dx = float(
        end.x
    ) - float(
        start.x
    )

    dy = float(
        end.y
    ) - float(
        start.y
    )

    dz = float(
        end.z
    ) - float(
        start.z
    )

    return math.sqrt(
        dx * dx
        + dy * dy
        + dz * dz
    )


def point_at_parameter(
    start,
    end,
    parameter,
):
    """Return a 3D point at one normalized centerline parameter."""

    parameter = float(
        parameter
    )

    return Point3D(
        float(
            start.x
        )
        + parameter
        * (
            float(
                end.x
            )
            - float(
                start.x
            )
        ),
        float(
            start.y
        )
        + parameter
        * (
            float(
                end.y
            )
            - float(
                start.y
            )
        ),
        float(
            start.z
        )
        + parameter
        * (
            float(
                end.z
            )
            - float(
                start.z
            )
        ),
    )


def member_outside_diameter(
    member_object,
):
    """Return the selected member's positive outside diameter in millimeters."""

    try:
        diameter = quantity_value(
            member_object.OutsideDiameter
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
    ):
        return None

    if diameter <= 0.0:
        return None

    return diameter


def upright_snap_candidates(
    member_object,
    start,
    end,
):
    """
    Return ordered snap candidates along one selected member.

    Priority order is intentional:
    endpoint -> half-OD -> midpoint.

    Free placement is handled separately when no candidate is within the
    normal viewport snap distance.
    """

    candidates = [
        (
            0.0,
            "Endpoint",
        ),
        (
            1.0,
            "Endpoint",
        ),
    ]

    length = member_length(
        start,
        end,
    )

    diameter = member_outside_diameter(
        member_object
    )

    if (
        diameter is not None
        and length > 1e-9
    ):
        radius = (
            diameter
            / 2.0
        )

        radius_parameter = (
            radius
            / length
        )

        if (
            radius_parameter > 1e-9
            and radius_parameter < 0.5
        ):
            candidates.extend(
                [
                    (
                        radius_parameter,
                        (
                            "1/2 OD snap - "
                            f"{radius:.3f} mm from start"
                        ),
                    ),
                    (
                        1.0
                        - radius_parameter,
                        (
                            "1/2 OD snap - "
                            f"{radius:.3f} mm from end"
                        ),
                    ),
                ]
            )

    candidates.append(
        (
            0.5,
            "Midpoint",
        )
    )

    return tuple(
        candidates
    )


def screen_distance_to_point(
    view,
    mouse_position,
    point,
):
    """Return viewport pixel distance from the mouse to one 3D point."""

    if (
        view is None
        or mouse_position is None
        or point is None
    ):
        return None

    try:
        screen = (
            view.getPointOnScreen(
                FreeCAD.Vector(
                    point.x,
                    point.y,
                    point.z,
                )
            )
        )
    except Exception:
        return None

    return math.hypot(
        float(
            screen[
                0
            ]
        )
        - float(
            mouse_position[
                0
            ]
        ),
        float(
            screen[
                1
            ]
        )
        - float(
            mouse_position[
                1
            ]
        ),
    )


class UprightHeightDialog(
    QtGui.QDialog
):
    """Collect one positive upright height."""

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.setWindowTitle(
            "Create Upright"
        )

        self.setMinimumWidth(
            320
        )

        self.height_box = (
            QtGui.QDoubleSpinBox()
        )

        self.height_box.setRange(
            0.001,
            1_000_000.0,
        )

        self.height_box.setDecimals(
            3
        )

        self.height_box.setSingleStep(
            25.0
        )

        self.height_box.setValue(
            500.0
        )

        form = (
            QtGui.QFormLayout()
        )

        form.addRow(
            "Height (mm):",
            self.height_box,
        )

        note = QtGui.QLabel(
            "The upright will be created vertically in global +Z."
        )

        note.setWordWrap(
            True
        )

        buttons = (
            QtGui.QDialogButtonBox(
                QtGui.QDialogButtonBox.Ok
                | QtGui.QDialogButtonBox.Cancel
            )
        )

        buttons.button(
            QtGui.QDialogButtonBox.Ok
        ).setText(
            "Pick Start Point"
        )

        buttons.accepted.connect(
            self.accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout = (
            QtGui.QVBoxLayout()
        )

        layout.addLayout(
            form
        )

        layout.addWidget(
            note
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            buttons
        )

        self.setLayout(
            layout
        )

        self.height_box.setFocus()


class InteractiveCreateUprightTool:
    """Pick one point along a preselected member and create an upright."""

    def __init__(
        self,
        document,
        source_member,
        height,
    ):
        self.document = document
        self.source_member = source_member
        self.height = float(
            height
        )

        (
            self.start_point,
            self.end_point,
        ) = member_centerline(
            source_member
        )

        self.view = None
        self.status_bar = None

        self.mouse_callback = None
        self.move_callback = None
        self.keyboard_callback = None

        self.preview_object = None
        self.current_point = None
        self.current_snap_label = None

    def start(
        self,
    ):
        """Start upright-position selection."""

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
            "ForgeCAD Create Upright: move along the selected member, "
            "then click where the upright should start. Esc: Cancel."
        )

    def show_status(
        self,
        message,
    ):
        """Show one status-bar instruction."""

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
        """Remove the temporary upright preview."""

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
        """Show a vertical line for the proposed upright."""

        if point is None:
            self.remove_preview()
            return

        end = upright_end_point(
            point,
            self.height,
        )

        if self.preview_object is None:
            self.preview_object = (
                self.document.addObject(
                    "Part::Feature",
                    PREVIEW_OBJECT_NAME,
                )
            )

            self.preview_object.Label = (
                "Upright Preview"
            )

            try:
                self.preview_object.ViewObject.Selectable = False
                self.preview_object.ViewObject.LineWidth = 5.0
            except Exception:
                pass

        self.preview_object.Shape = (
            Part.makeLine(
                FreeCAD.Vector(
                    point.x,
                    point.y,
                    point.z,
                ),
                FreeCAD.Vector(
                    end.x,
                    end.y,
                    end.z,
                ),
            )
        )

        self.document.recompute()

    def stop(
        self,
    ):
        """Stop upright mode and remove callbacks/preview."""

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

        self.current_point = None
        self.current_snap_label = None

        if self.status_bar is not None:
            try:
                self.status_bar.clearMessage()
            except Exception:
                pass

        self.status_bar = None
        self.view = None

        if _active_tool is self:
            _active_tool = None

    def resolve_point(
        self,
        position,
    ):
        """
        Return a point on the member with fabrication-friendly snapping.

        Snap priority:
        endpoint -> half outside diameter -> midpoint -> free.
        """

        (
            free_point,
            distance,
            parameter,
        ) = screen_point_on_segment(
            self.view,
            position,
            self.start_point,
            self.end_point,
        )

        if (
            free_point is None
            or distance is None
            or parameter is None
        ):
            self.current_snap_label = None
            return None

        if (
            distance
            > SNAP_DISTANCE_PIXELS
        ):
            self.current_snap_label = None
            return None

        for (
            snap_parameter,
            snap_label,
        ) in upright_snap_candidates(
            self.source_member,
            self.start_point,
            self.end_point,
        ):
            snap_point = point_at_parameter(
                self.start_point,
                self.end_point,
                snap_parameter,
            )

            snap_distance = (
                screen_distance_to_point(
                    self.view,
                    position,
                    snap_point,
                )
            )

            if (
                snap_distance is not None
                and snap_distance
                <= SNAP_DISTANCE_PIXELS
            ):
                self.current_snap_label = (
                    snap_label
                )

                return snap_point

        self.current_snap_label = (
            "Free position"
        )

        return free_point

    def on_mouse_move(
        self,
        event,
    ):
        """Update the proposed upright position."""

        point = self.resolve_point(
            event.get(
                "Position"
            )
        )

        self.current_point = point

        self.update_preview(
            point
        )

        if point is None:
            self.show_status(
                "ForgeCAD Create Upright: move onto the selected member "
                "centerline. Esc: Cancel."
            )
            return

        snap_label = (
            self.current_snap_label
            or "Free position"
        )

        self.show_status(
            "ForgeCAD Create Upright: "
            f"{snap_label} - "
            f"start ({point.x:.3f}, {point.y:.3f}, {point.z:.3f}), "
            f"height {self.height:.3f} mm - click to create. Esc: Cancel."
        )

    def on_mouse_event(
        self,
        event,
    ):
        """Create the upright on left-button press."""

        if event.get(
            "State"
        ) != "DOWN":
            return

        if event.get(
            "Button"
        ) != "BUTTON1":
            return

        point = self.resolve_point(
            event.get(
                "Position"
            )
        )

        if point is None:
            return

        self.stop()

        transaction_started = False

        try:
            if hasattr(
                self.document,
                "openTransaction",
            ):
                self.document.openTransaction(
                    "Create ForgeCAD Upright"
                )

                transaction_started = True

            (
                layout_object,
                member_object,
                start_node,
                end_node,
            ) = create_upright(
                self.document,
                point,
                self.height,
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
            RuntimeError,
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
                "Create Upright Failed",
                str(
                    error
                ),
            )
            return

        FreeCADGui.Selection.clearSelection()

        FreeCADGui.Selection.addSelection(
            member_object
        )

    def on_keyboard_event(
        self,
        event,
    ):
        """Cancel upright mode with Escape."""

        if event.get(
            "State"
        ) != "DOWN":
            return

        key = str(
            event.get(
                "Key",
                "",
            )
        ).upper()

        if key in (
            "ESC",
            "ESCAPE",
        ):
            self.stop()


class CreateUprightCommand:
    """Create a global-Z upright from a point on a straight member."""

    def GetResources(
        self,
    ):
        return {
            "MenuText": "Create Upright",
            "ToolTip": (
                "Create a vertical ForgeCAD member from any picked "
                "point along a selected straight member"
            ),
        }

    def Activated(
        self,
    ):
        global _active_tool

        document = FreeCAD.ActiveDocument

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Document",
                "Open or create a ForgeCAD project first.",
            )
            return

        selection = list(
            FreeCADGui.Selection.getSelection()
        )

        if (
            len(
                selection
            )
            != 1
            or not is_forgecad_member(
                selection[
                    0
                ]
            )
        ):
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select One Member",
                (
                    "Select exactly one straight ForgeCAD member first. "
                    "The upright can start anywhere along that member."
                ),
            )
            return

        dialog = UprightHeightDialog(
            FreeCADGui.getMainWindow()
        )

        if (
            dialog.exec_()
            != QtGui.QDialog.Accepted
        ):
            return

        if _active_tool is not None:
            _active_tool.stop()

        _active_tool = (
            InteractiveCreateUprightTool(
                document,
                selection[
                    0
                ],
                dialog.height_box.value(),
            )
        )

        _active_tool.start()

    def IsActive(
        self,
    ):
        return FreeCAD.ActiveDocument is not None


def register_command() -> None:
    """Register the Create Upright command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        CreateUprightCommand(),
    )
