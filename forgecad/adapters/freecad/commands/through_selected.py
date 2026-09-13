"""FreeCAD command: keep the first selected tube through and cope branches to it."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.commands.generate_from_selection import regenerate_frame
from forgecad.adapters.freecad.commands.inspect_joint import InspectionNode, node_object_at_position
from forgecad.adapters.freecad.joint_inspector_adapter import (
    joint_from_node_object,
    structural_member_from_freecad_object,
)
from forgecad.adapters.freecad.joint_treatment_store import (
    load_joint_cope_pairs,
    load_joint_through_pairs,
    load_joint_treatment,
    replace_joint_cope_pairs,
    replace_joint_through_pairs,
    vector_key,
)
from forgecad.fabrication import Joint
from forgecad.services.joint_treatment_resolver import CopeInstruction
from forgecad.services.notch_analysis import build_cope_specification
from forgecad.services.selected_through import (
    remove_source_pairs,
    replace_branch_pairs,
    selected_through_request,
    validate_primary_compatibility,
)

COMMAND_NAME = "ForgeCAD_ThroughSelected"


def _layout_id(obj):
    return str(getattr(obj, "SourceLayoutID", "") or "").strip()


def _warn(title, message):
    QtGui.QMessageBox.warning(FreeCADGui.getMainWindow(), title, str(message))


def _preflight(document, selection, node_xyz, through_id, branch_ids):
    position = FreeCAD.Vector(*node_xyz)
    node_object = node_object_at_position(document, position)
    if node_object is None:
        node_object = InspectionNode("Joint", position)
    detected = joint_from_node_object(document, node_object)
    if detected.member_count < 2:
        raise ValueError("No ForgeCAD joint exists at the selected connection point.")

    selected_by_id = {_layout_id(obj): obj for obj in selection}
    needed = (through_id,) + tuple(branch_ids)
    if any(ident not in selected_by_id for ident in needed):
        raise ValueError("Could not resolve the selected ForgeCAD members.")

    by_id = {
        ident: structural_member_from_freecad_object(selected_by_id[ident])
        for ident in needed
    }
    selected_joint = Joint(
        node=detected.node,
        members=[by_id[ident] for ident in needed],
    )

    node_key_value = vector_key(position)
    validate_primary_compatibility(
        load_joint_treatment(document, node_key_value),
        needed,
    )

    through_member = by_id[through_id]
    for branch_id in branch_ids:
        build_cope_specification(
            CopeInstruction(
                joint=selected_joint,
                coped_member=by_id[branch_id],
                target_member=through_member,
            )
        )
    return node_key_value


def apply_selected_through(document, selection):
    """Persist direct through relationships and regenerate atomically."""
    selection = list(selection or ())
    node_xyz, through_id, branch_ids = selected_through_request(selection)
    node_key_value = _preflight(
        document, selection, node_xyz, through_id, branch_ids
    )

    # Phase 3 stored Through as ordinary explicit cope pairs. Remove any
    # selected-source pairs there so rerunning this command migrates the joint
    # into the dedicated through store without leaving duplicate cuts.
    generic_copes = load_joint_cope_pairs(document, node_key_value)
    remaining_generic_copes = remove_source_pairs(generic_copes, branch_ids)

    existing_through = load_joint_through_pairs(document, node_key_value)
    updated_through = replace_branch_pairs(existing_through, through_id, branch_ids)

    started = False
    try:
        document.openTransaction("Through Selected ForgeCAD Members")
        started = True
        if remaining_generic_copes != tuple(generic_copes):
            replace_joint_cope_pairs(document, node_key_value, remaining_generic_copes)
        replace_joint_through_pairs(document, node_key_value, updated_through)
        FreeCADGui.Selection.clearSelection()
        regenerate_frame(document)
        document.commitTransaction()
        started = False
    except Exception:
        if started:
            document.abortTransaction()
        raise
    return through_id, branch_ids


class ThroughSelectedCommand:
    def GetResources(self):
        return {
            "MenuText": "Through Selected",
            "ToolTip": (
                "Select the tube that stays through first, then branch tube(s) ending at it. "
                "Corners are extended to the far outside wall; interior T-joints need no extension."
            ),
        }

    def Activated(self):
        document = FreeCAD.ActiveDocument
        if document is None:
            _warn("Through Selected", "Open a ForgeCAD project first.")
            return
        try:
            through_id, branch_ids = apply_selected_through(
                document, list(FreeCADGui.Selection.getSelection())
            )
        except Exception as error:
            _warn("Through Selected", error)
            return
        FreeCAD.Console.PrintMessage(
            "ForgeCAD: kept " + through_id + " through and coped "
            + str(len(branch_ids)) + " selected branch tube(s) to it.\n"
        )

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


def register_command():
    FreeCADGui.addCommand(COMMAND_NAME, ThroughSelectedCommand())
