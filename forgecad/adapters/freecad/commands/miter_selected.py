"""FreeCAD command: miter exactly two selected ForgeCAD members."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.commands.generate_from_selection import regenerate_frame
from forgecad.adapters.freecad.commands.inspect_joint import (
    InspectionNode,
    connected_member_objects,
    joint_from_node_object,
    node_object_at_position,
)
from forgecad.adapters.freecad.joint_inspector_adapter import (
    structural_member_from_freecad_object,
)
from forgecad.adapters.freecad.joint_treatment_store import (
    save_joint_treatment,
    vector_key,
)
from forgecad.fabrication import Joint
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
    JointTreatmentMode,
)
from forgecad.services.joint_extension import extension_specifications_for_treatment
from forgecad.services.joint_miter import miter_specifications_for_treatment
from forgecad.services.selected_miter import selected_miter_request


COMMAND_NAME = "ForgeCAD_MiterSelected"


def _layout_id(obj):
    return str(getattr(obj, "SourceLayoutID", "") or "").strip()


def _warn(title, message):
    QtGui.QMessageBox.warning(
        FreeCADGui.getMainWindow(),
        title,
        str(message),
    )


def _joint_context(document, node_xyz):
    position = FreeCAD.Vector(*node_xyz)
    node_object = node_object_at_position(document, position)
    if node_object is None:
        node_object = InspectionNode("Joint", position)

    detected = joint_from_node_object(document, node_object)
    if detected.member_count < 2:
        raise ValueError("No ForgeCAD joint exists at the shared endpoint.")

    objects = connected_member_objects(document, node_object)
    domain_members = []
    by_id = {}
    for obj in objects:
        ident = _layout_id(obj)
        if not ident:
            continue
        member = structural_member_from_freecad_object(obj)
        domain_members.append(member)
        by_id[ident] = member

    joint = Joint(node=detected.node, members=domain_members)
    return joint, by_id, position


def _preflight(document, node_xyz, member_ids):
    joint, by_id, position = _joint_context(document, node_xyz)
    missing = [ident for ident in member_ids if ident not in by_id]
    if missing:
        raise ValueError(
            "One selected tube was not resolved as a member of this joint. "
            "Select the generated frame members themselves."
        )

    first = by_id[member_ids[0]]
    second = by_id[member_ids[1]]
    treatment = JointTreatment.both_coped(joint, first, second)

    # Use the same fabrication services as regeneration. This rejects collinear
    # or otherwise invalid pairs before anything is written to the document.
    specifications = miter_specifications_for_treatment(treatment)
    if len(specifications) != 2:
        raise ValueError("The selected pair cannot produce a two-member miter.")
    extension_specifications_for_treatment(treatment)

    return vector_key(position)


def apply_selected_miter(document, selection):
    """Save one explicit miter pair and regenerate in one FreeCAD transaction.

    save_joint_treatment updates only the primary treatment fields. Existing
    ExplicitCopePairs on the same persistent treatment object are preserved.
    """
    node_xyz, member_ids = selected_miter_request(selection)
    node_key_value = _preflight(document, node_xyz, member_ids)

    started = False
    try:
        document.openTransaction("Miter Selected ForgeCAD Members")
        started = True
        save_joint_treatment(
            document,
            node_key_value,
            JointTreatmentMode.BOTH_COPED,
            member_ids,
        )
        FreeCADGui.Selection.clearSelection()
        regenerate_frame(document)
        document.commitTransaction()
        started = False
    except Exception:
        if started:
            document.abortTransaction()
        raise

    return member_ids


class MiterSelectedCommand:
    def GetResources(self):
        return {
            "MenuText": "Miter Selected",
            "ToolTip": (
                "Select two generated ForgeCAD tubes that share an endpoint, "
                "then miter that pair. Other members and additive copes at the "
                "same joint are preserved."
            ),
        }

    def Activated(self):
        document = FreeCAD.ActiveDocument
        if document is None:
            _warn("Miter Selected", "Open a ForgeCAD project first.")
            return

        selection = list(FreeCADGui.Selection.getSelection())
        try:
            member_ids = apply_selected_miter(document, selection)
        except Exception as error:
            _warn("Miter Selected", error)
            return

        FreeCAD.Console.PrintMessage(
            "ForgeCAD: mitered selected pair "
            + member_ids[0]
            + " + "
            + member_ids[1]
            + ". Existing additive copes were preserved.\n"
        )

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


def register_command():
    FreeCADGui.addCommand(COMMAND_NAME, MiterSelectedCommand())
