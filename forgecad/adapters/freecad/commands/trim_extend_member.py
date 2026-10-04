"""Interactive FreeCAD command for trimming/extending ForgeCAD structural members."""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui

from forgecad.adapters.freecad.joint_inspector_adapter import (
    is_forgecad_bent_member,
    structural_member_from_freecad_object,
)
from forgecad.adapters.freecad.member_trim_extend_adapter import (
    trim_extend_member_object,
)
from forgecad.services.member_trim_extend import (
    line_intersection_3d,
    modification_kind,
    straight_to_bent_endpoint_intersection_3d,
)


COMMAND_NAME = "ForgeCAD_TrimExtendMember"

_active_tool = None


def is_forgecad_member(
    obj,
):
    """Return True for a generated straight or converted bent ForgeCAD member."""

    if obj is None:
        return False

    if is_forgecad_bent_member(
        obj
    ):
        return True

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



def selected_source_member():
    """Return exactly one selected ForgeCAD structural member."""

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


def screen_distance_squared(
    first,
    second,
):
    """Return squared 2D screen distance."""

    dx = (
        float(
            first[
                0
            ]
        )
        - float(
            second[
                0
            ]
        )
    )

    dy = (
        float(
            first[
                1
            ]
        )
        - float(
            second[
                1
            ]
        )
    )

    return (
        dx * dx
        + dy * dy
    )


def endpoint_nearest_screen_position(
    view,
    member,
    position,
):
    """Return start/end according to which source endpoint was clicked nearer."""

    start_screen = (
        view.getPointOnScreen(
            FreeCAD.Vector(
                member.start.x,
                member.start.y,
                member.start.z,
            )
        )
    )

    end_screen = (
        view.getPointOnScreen(
            FreeCAD.Vector(
                member.end.x,
                member.end.y,
                member.end.z,
            )
        )
    )

    if (
        screen_distance_squared(
            position,
            start_screen,
        )
        <= screen_distance_squared(
            position,
            end_screen,
        )
    ):
        return "start"

    return "end"


def defer_call(
    callback,
):
    """
    Run work after the current Qt/Coin callback has returned.

    Document mutation must not happen while FreeCAD is still inside a
    selection or Coin event callback. A zero-delay Qt timer schedules the
    operation for the next GUI event-loop turn.
    """

    QtCore.QTimer.singleShot(
        0,
        callback,
    )


class TrimExtendSelectionObserver:
    """Receive the target member selected after command activation."""

    def __init__(
        self,
        tool,
    ):
        self.tool = tool

    def addSelection(
        self,
        document_name,
        object_name,
        sub_name,
        point,
    ):
        self.tool.target_selected(
            document_name,
            object_name,
        )


class InteractiveTrimExtendTool:
    """Select a target member, then resolve trim-side intent if necessary."""

    def __init__(
        self,
        document,
        source_object,
    ):
        self.document = document
        self.source_object = (
            source_object
        )

        self.source_member = (
            structural_member_from_freecad_object(
                source_object
            )
        )

        self.view = None
        self.status_bar = None
        self.selection_observer = None

        self.keyboard_callback = None
        self.trim_click_callback = None

        self.target_object = None
        self.target_member = None
        self.target_endpoint = None
        self.awaiting_bent_target_endpoint = False
        self.intersection = None
        self.source_parameter = None

        self.stopped = False
        self.commit_pending = False

    def show_status(
        self,
        message,
    ):
        if self.status_bar is not None:
            self.status_bar.showMessage(
                message
            )

    def add_keyboard_callback(
        self,
    ):
        if (
            self.view is None
            or self.keyboard_callback is not None
        ):
            return

        self.keyboard_callback = (
            self.view.addEventCallback(
                "SoKeyboardEvent",
                self.on_keyboard_event,
            )
        )

    def remove_keyboard_callback(
        self,
    ):
        if (
            self.view is None
            or self.keyboard_callback is None
        ):
            return

        callback = (
            self.keyboard_callback
        )

        self.keyboard_callback = None

        try:
            self.view.removeEventCallback(
                "SoKeyboardEvent",
                callback,
            )
        except Exception:
            pass

    def add_trim_click_callback(
        self,
    ):
        if (
            self.view is None
            or self.trim_click_callback is not None
        ):
            return

        self.trim_click_callback = (
            self.view.addEventCallback(
                "SoMouseButtonEvent",
                self.on_trim_side_click,
            )
        )

    def remove_trim_click_callback(
        self,
    ):
        if (
            self.view is None
            or self.trim_click_callback is None
        ):
            return

        callback = (
            self.trim_click_callback
        )

        self.trim_click_callback = None

        try:
            self.view.removeEventCallback(
                "SoMouseButtonEvent",
                callback,
            )
        except Exception:
            pass

    def add_selection_observer(
        self,
    ):
        if self.selection_observer is not None:
            return

        self.selection_observer = (
            TrimExtendSelectionObserver(
                self
            )
        )

        FreeCADGui.Selection.addObserver(
            self.selection_observer
        )

    def remove_selection_observer(
        self,
    ):
        if self.selection_observer is None:
            return

        observer = (
            self.selection_observer
        )

        self.selection_observer = None

        try:
            FreeCADGui.Selection.removeObserver(
                observer
            )
        except Exception:
            pass

    def start(
        self,
    ):
        """Begin waiting for the target-member selection."""

        self.view = (
            FreeCADGui.activeDocument()
            .activeView()
        )

        self.status_bar = (
            FreeCADGui.getMainWindow()
            .statusBar()
        )

        self.add_selection_observer()
        self.add_keyboard_callback()

        FreeCADGui.Selection.clearSelection()

        self.show_status(
            "Trim / Extend: the highlighted member will be changed. "
            "Select the member to use as the target. ForgeCAD will "
            "automatically Extend if the target is beyond an end, or "
            "switch to Trim if the target crosses the member. "
            "Press Esc to cancel."
        )

    def stop(
        self,
    ):
        """Stop the command and remove every observer/callback safely."""

        global _active_tool

        if self.stopped:
            return

        self.stopped = True
        self.commit_pending = False

        self.remove_selection_observer()
        self.remove_trim_click_callback()
        self.remove_keyboard_callback()

        if self.status_bar is not None:
            try:
                self.status_bar.clearMessage()
            except Exception:
                pass

        self.status_bar = None
        self.view = None

        if _active_tool is self:
            _active_tool = None

    def object_from_selection(
        self,
        document_name,
        object_name,
    ):
        """Resolve a FreeCAD object selected by the observer."""

        try:
            selected_document = (
                FreeCAD.getDocument(
                    document_name
                )
            )
        except Exception:
            selected_document = (
                self.document
            )

        if selected_document is None:
            return None

        try:
            return selected_document.getObject(
                object_name
            )
        except Exception:
            return None

    def target_selected(
        self,
        document_name,
        object_name,
    ):
        """
        Commit Trim / Extend immediately after the destination member is picked.

        Workflow for every member combination:
        select source -> run Trim / Extend -> click destination.
        """

        if (
            self.stopped
            or self.commit_pending
        ):
            return

        target = self.object_from_selection(
            document_name,
            object_name,
        )

        if (
            target is None
            or not is_forgecad_member(
                target
            )
        ):
            self.show_status(
                "ForgeCAD Trim / Extend: select the ForgeCAD member "
                "you want the source to reach. Press Esc to cancel."
            )
            return

        if target is self.source_object:
            self.show_status(
                "ForgeCAD Trim / Extend: target must be a different "
                "member. Press Esc to cancel."
            )
            return

        self.target_object = target
        self.commit_pending = True
        self.remove_selection_observer()

        self.show_status(
            "Trim / Extend: destination selected. ForgeCAD is choosing "
            "the nearest valid source end automatically."
        )

        defer_call(
            lambda: self.commit(
                endpoint=None
            )
        )





    def commit(
        self,
        endpoint,
    ):
        """Perform the safe replacement outside any selection/Coin callback."""

        if self.stopped:
            return

        transaction_started = False

        try:
            if hasattr(self.document, "openTransaction"):
                self.document.openTransaction(
                    "Trim / Extend ForgeCAD Member"
                )
                transaction_started = True

            result = trim_extend_member_object(
                self.document,
                self.source_object,
                self.target_object,
                endpoint=endpoint,
                target_endpoint=getattr(
                    self,
                    "target_endpoint",
                    None,
                ),
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

            self.commit_pending = False
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Trim / Extend Member Failed",
                str(error),
            )
            self.stop()
            return

        replacement_object = result[1]
        self.stop()

        try:
            FreeCADGui.Selection.clearSelection()
        except Exception:
            pass

        try:
            FreeCADGui.Selection.addSelection(
                replacement_object
            )
        except Exception:
            pass


    def on_trim_side_click(
        self,
        event,
    ):
        """
        Resolve bent-target endpoint selection and source endpoint intent,
        then defer document mutation.
        """

        if (
            self.stopped
            or self.commit_pending
        ):
            return

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

        if position is None:
            return

        if getattr(
            self,
            "awaiting_bent_target_endpoint",
            False,
        ):
            target_endpoint = (
                endpoint_nearest_screen_position(
                    self.view,
                    self.target_member,
                    position,
                )
            )

            self.target_endpoint = (
                target_endpoint
            )
            self.awaiting_bent_target_endpoint = False

            if is_forgecad_bent_member(
                self.source_object
            ):
                self.show_status(
                    "Bent-to-bent Trim / Extend: target end selected. "
                    "Now click the END of the bent SOURCE you want to move."
                )
                return

            try:
                (
                    intersection,
                    source_parameter,
                    _target_parameter,
                ) = straight_to_bent_endpoint_intersection_3d(
                    self.source_member,
                    self.target_member,
                    target_endpoint,
                )

            except ValueError as error:
                QtGui.QMessageBox.warning(
                    FreeCADGui.getMainWindow(),
                    "Trim / Extend Member",
                    str(
                        error
                    ),
                )
                self.stop()
                return

            kind = modification_kind(
                source_parameter
            )

            if kind == "none":
                QtGui.QMessageBox.information(
                    FreeCADGui.getMainWindow(),
                    "Trim / Extend Member",
                    (
                        "The selected bent-target tangent already intersects "
                        "the source at its endpoint."
                    ),
                )
                self.stop()
                return

            self.intersection = (
                intersection
            )
            self.source_parameter = (
                source_parameter
            )

            if kind == "extend":
                self.commit_pending = True
                self.remove_trim_click_callback()
                self.show_status(
                    "Extend: bent target endpoint selected. ForgeCAD is "
                    "extending the straight member to that local tangent."
                )
                defer_call(
                    lambda: self.commit(
                        endpoint=None
                    )
                )
                return

            self.show_status(
                "Trim: bent target endpoint selected. Now click the portion "
                "of the straight source you want to REMOVE."
            )
            return

        endpoint = (
            endpoint_nearest_screen_position(
                self.view,
                self.source_member,
                position,
            )
        )

        self.commit_pending = True
        self.remove_trim_click_callback()

        if is_forgecad_bent_member(
            self.source_object
        ):
            self.show_status(
                "Bent Trim / Extend: moving the selected end to the target."
            )
        else:
            self.show_status(
                "Trim: portion selected. ForgeCAD is trimming that end back "
                "to the target and keeping the opposite side."
            )

        defer_call(
            lambda: self.commit(
                endpoint=endpoint
            )
        )




    def on_keyboard_event(
        self,
        event,
    ):
        """Cancel with Escape."""

        if self.stopped:
            return

        if event.get(
            "State"
        ) != "DOWN":
            return

        if event.get(
            "Key"
        ) not in (
            "ESCAPE",
            "ESC",
        ):
            return

        # Do not remove the keyboard callback from inside itself.
        defer_call(
            self.stop
        )


class TrimExtendMemberCommand:
    """Trim or extend one selected ForgeCAD member to another."""

    def GetResources(
        self,
    ):
        return {
            "MenuText": "Trim / Extend Member",
            "ToolTip": (
                "Trim or extend one selected ForgeCAD member "
                "to the centerline of a straight target member"
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
                "Open or create a ForgeCAD project first.",
            )
            return

        source = (
            selected_source_member()
        )

        if source is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Select One Member",
                (
                    "Select exactly one ForgeCAD member to modify, "
                    "then run Trim / Extend Member."
                ),
            )
            return

        if _active_tool is not None:
            _active_tool.stop()

        _active_tool = (
            InteractiveTrimExtendTool(
                document,
                source,
            )
        )

        _active_tool.start()

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Trim / Extend Member command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        TrimExtendMemberCommand(),
    )
