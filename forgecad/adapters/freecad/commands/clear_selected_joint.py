"""FreeCAD command: clear only the selected ForgeCAD joint operation(s)."""

import time

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.commands.generate_from_selection import regenerate_frame
from forgecad.adapters.freecad.commands.inspect_joint import (
    InspectionNode,
    node_object_at_position,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    frame_member_objects,
)
from forgecad.adapters.freecad.joint_treatment_store import (
    load_joint_cope_pairs,
    load_joint_through_pairs,
    load_joint_treatment,
    replace_joint_cope_pairs,
    replace_joint_through_pairs,
    save_joint_treatment,
    vector_key,
)
from forgecad.fabrication.joint_treatment import JointTreatmentMode
from forgecad.services.selected_joint_clear import (
    clear_selected_operation_plan,
    selected_clear_request,
)
from forgecad.services.selected_through import point_on_segment

COMMAND_NAME = "ForgeCAD_ClearSelectedJoint"


def _layout_id(obj):
    return str(getattr(obj, "SourceLayoutID", "") or "").strip()


def _xyz(point):
    return (float(point.x), float(point.y), float(point.z))


def _warn(title, message):
    QtGui.QMessageBox.warning(FreeCADGui.getMainWindow(), title, str(message))


def _joint_member_ids(
    document,
    node_xyz,
):
    """
    Return persistent fabrication identities participating at one joint.

    Straight members may participate at an endpoint or, for Through behavior,
    through their interior. Bent members participate only at their true solved
    endpoints and use Start/EndFabricationLayoutID.
    """

    from forgecad.services.fabrication_identity import (
        fabrication_layout_id_at_point,
    )

    position = FreeCAD.Vector(
        *node_xyz
    )

    result = []

    for obj in frame_member_objects(
        document
    ):
        try:
            ident = fabrication_layout_id_at_point(
                obj,
                position,
            )
        except ValueError:
            ident = str(
                getattr(
                    obj,
                    "SourceLayoutID",
                    "",
                )
                or ""
            ).strip()

            if not ident:
                continue

            if (
                not hasattr(
                    obj,
                    "StartPoint",
                )
                or not hasattr(
                    obj,
                    "EndPoint",
                )
            ):
                continue

            if not point_on_segment(
                node_xyz,
                _xyz(
                    obj.StartPoint
                ),
                _xyz(
                    obj.EndPoint
                ),
            ):
                continue

        if (
            ident
            and ident
            not in result
        ):
            result.append(
                ident
            )

    return tuple(
        result
    )



def apply_clear_selected_joint(
    document,
    selection,
):
    """
    Clear only the selected saved fabrication relationship.

    When a converted bent tube participates, refresh fabrication in-place
    rather than regenerating the layout-derived Frame group. Regeneration can
    recreate source straight members consumed by bend conversion.

    Straight-only behavior retains the proven regeneration path.
    """

    selection = list(
        selection
        or ()
    )

    node_xyz, selected_ids = (
        selected_clear_request(
            selection
        )
    )

    position = FreeCAD.Vector(
        *node_xyz
    )

    node_key_value = vector_key(
        position
    )

    saved = load_joint_treatment(
        document,
        node_key_value,
    )

    existing_copes = (
        load_joint_cope_pairs(
            document,
            node_key_value,
        )
    )

    existing_throughs = (
        load_joint_through_pairs(
            document,
            node_key_value,
        )
    )

    (
        clear_primary,
        remaining_copes,
        removed_copes,
        remaining_throughs,
        removed_throughs,
    ) = clear_selected_operation_plan(
        saved,
        existing_copes,
        selected_ids,
        _joint_member_ids(
            document,
            node_xyz,
        ),
        existing_throughs,
    )

    has_bent_member = any(
        (
            not str(
                getattr(
                    obj,
                    "SourceLayoutID",
                    "",
                )
                or ""
            ).strip()
            and (
                bool(
                    str(
                        getattr(
                            obj,
                            "StartFabricationLayoutID",
                            "",
                        )
                        or ""
                    ).strip()
                )
                or bool(
                    str(
                        getattr(
                            obj,
                            "EndFabricationLayoutID",
                            "",
                        )
                        or ""
                    ).strip()
                )
                or bool(
                    getattr(
                        obj,
                        "SourceLayoutLines",
                        (),
                    )
                )
            )
        )
        for obj in selection
    )

    started = False

    try:
        document.openTransaction(
            "Clear Selected ForgeCAD Joint Treatment"
        )
        started = True

        if clear_primary:
            save_joint_treatment(
                document,
                node_key_value,
                JointTreatmentMode.AUTO,
                (),
            )

        if removed_copes:
            replace_joint_cope_pairs(
                document,
                node_key_value,
                remaining_copes,
            )

        if removed_throughs:
            replace_joint_through_pairs(
                document,
                node_key_value,
                remaining_throughs,
            )

        FreeCADGui.Selection.clearSelection()

        if has_bent_member:
            from forgecad.adapters.freecad.fabrication_refresh import (
                refresh_fabrication_for_document,
            )

            refresh_fabrication_for_document(
                document
            )
        else:
            regenerate_frame(
                document
            )

        document.commitTransaction()
        started = False

    except Exception:
        if started:
            document.abortTransaction()
        raise

    return (
        clear_primary,
        removed_copes,
        removed_throughs,
    )



class ClearSelectedJointCommand:
    """Clear one selected fabrication operation without duplicate activation noise."""

    DUPLICATE_EMPTY_WINDOW_SECONDS = 1.0

    def __init__(self):
        self._activated = False
        self._suppress_empty_until = 0.0

    def GetResources(self):
        return {
            "MenuText": "Clear Selected Treatment",
            "ToolTip": (
                "Select the tubes in the same order used to create the operation. "
                "Miter, Cope, and Through relationships are cleared without touching unrelated operations."
            ),
        }

    def Activated(self):
        # FreeCAD may deliver a second activation while/just after regeneration
        # and selection clearing. Never let that duplicate invocation become a
        # misleading "select tubes" error after a successful clear.
        if self._activated:
            return

        selection = list(FreeCADGui.Selection.getSelection())
        now = time.monotonic()
        if not selection and now < self._suppress_empty_until:
            self._suppress_empty_until = 0.0
            return

        document = FreeCAD.ActiveDocument
        if document is None:
            _warn("Clear Selected Treatment", "Open a ForgeCAD project first.")
            return

        self._activated = True
        try:
            try:
                cleared_primary, removed_copes, removed_throughs = apply_clear_selected_joint(
                    document,
                    selection,
                )
            except Exception as error:
                _warn("Clear Selected Treatment", error)
                return

            parts = []
            if cleared_primary:
                parts.append("miter")
            if removed_copes:
                parts.append(str(len(removed_copes)) + " cope(s)")
            if removed_throughs:
                parts.append(str(len(removed_throughs)) + " through relationship(s)")
            FreeCAD.Console.PrintMessage(
                "ForgeCAD: cleared selected " + " and ".join(parts) + ".\n"
            )

            # The successful clear intentionally removed the selection before
            # regeneration. Suppress only an immediate empty duplicate command
            # activation; a later normal empty invocation still reports usage.
            self._suppress_empty_until = (
                time.monotonic() + self.DUPLICATE_EMPTY_WINDOW_SECONDS
            )
        finally:
            self._activated = False


def register_command():
    FreeCADGui.addCommand(COMMAND_NAME, ClearSelectedJointCommand())
