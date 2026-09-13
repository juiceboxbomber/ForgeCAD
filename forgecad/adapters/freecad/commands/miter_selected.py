"""FreeCAD command: miter exactly two selected ForgeCAD members."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.commands.generate_from_selection import regenerate_frame
from forgecad.adapters.freecad.fabrication_refresh import (
    refresh_fabrication_for_document,
)
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


def _joint_context(
    document,
    node_xyz,
):
    position = FreeCAD.Vector(
        *node_xyz
    )

    node_object = (
        node_object_at_position(
            document,
            position,
        )
    )

    if node_object is None:
        node_object = InspectionNode(
            "Joint",
            position,
        )

    detected = joint_from_node_object(
        document,
        node_object,
    )

    if detected.member_count < 2:
        raise ValueError(
            "No ForgeCAD joint exists at the shared endpoint."
        )

    objects = connected_member_objects(
        document,
        node_object,
    )

    domain_members = []
    by_id = {}

    from forgecad.services.fabrication_identity import (
        fabrication_layout_id_at_point,
    )

    for obj in objects:
        try:
            ident = (
                fabrication_layout_id_at_point(
                    obj,
                    position,
                )
            )
        except ValueError:
            continue

        member = (
            structural_member_from_freecad_object(
                obj
            )
        )

        domain_members.append(
            member
        )
        by_id[
            ident
        ] = member

    joint = Joint(
        node=detected.node,
        members=domain_members,
    )

    return (
        joint,
        by_id,
        position,
    )



def _preflight(
    document,
    node_xyz,
    member_ids,
    selection,
):
    """Validate the explicitly selected pair without global joint lookup."""
    from forgecad.fabrication import Joint, Node

    selection = list(selection or ())
    if len(selection) != 2:
        raise ValueError("Select exactly two tubes to miter together.")
    if len(member_ids) != 2:
        raise ValueError("Miter Selected requires exactly two persistent member identities.")

    domain_members = [
        structural_member_from_freecad_object(obj)
        for obj in selection
    ]

    node = Node(
        float(node_xyz[0]),
        float(node_xyz[1]),
        float(node_xyz[2]),
    )
    joint = Joint(
        node=node,
        members=domain_members,
    )
    treatment = JointTreatment.both_coped(
        joint,
        domain_members[0],
        domain_members[1],
    )

    specifications = miter_specifications_for_treatment(treatment)
    if len(specifications) != 2:
        raise ValueError("The selected pair cannot produce a two-member miter.")

    extension_specifications_for_treatment(treatment)
    position = FreeCAD.Vector(*node_xyz)
    return vector_key(position)



def apply_selected_miter(
    document,
    selection,
):
    """Save one explicit miter pair and update its structural objects."""
    selection = list(selection or ())
    node_xyz, member_ids = selected_miter_request(selection)
    node_key_value = _preflight(
        document,
        node_xyz,
        member_ids,
        selection,
    )

    has_bent_member = any(
        (
            not str(getattr(obj, "SourceLayoutID", "") or "").strip()
            and (
                bool(str(getattr(obj, "StartFabricationLayoutID", "") or "").strip())
                or bool(str(getattr(obj, "EndFabricationLayoutID", "") or "").strip())
                or bool(getattr(obj, "SourceLayoutLines", ()))
            )
        )
        for obj in selection
    )

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

        if has_bent_member:
            # Do not regenerate consumed layout lines back into straight tubes.
            refresh_fabrication_for_document(document)
        else:
            # Preserve the proven straight-member path.
            regenerate_frame(document)
            refresh_fabrication_for_document(document)

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
