"""FreeCAD command: cope one selected member to one to three selected targets."""

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
    load_joint_cope_pairs,
    load_joint_treatment,
    replace_joint_cope_pairs,
    vector_key,
)
from forgecad.fabrication import Joint
from forgecad.services.joint_treatment_resolver import CopeInstruction
from forgecad.services.notch_analysis import build_cope_specification
from forgecad.services.selected_cope import (
    replace_source_pairs,
    selected_cope_request,
)


COMMAND_NAME = "ForgeCAD_CopeSelected"


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
    """Build one endpoint-aware joint context for straight and bent members."""

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

    from forgecad.services.fabrication_identity import (
        fabrication_layout_id_at_point,
    )

    by_id = {}
    domain_members = []

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

        by_id[
            ident
        ] = member

        domain_members.append(
            member
        )

    return (
        Joint(
            node=detected.node,
            members=domain_members,
        ),
        by_id,
    )



def _preflight(document, node_xyz, source_id, target_ids):
    node_key_value = vector_key(FreeCAD.Vector(*node_xyz))
    saved = load_joint_treatment(document, node_key_value)
    if saved is not None:
        mode, primary_ids = saved
        if str(mode) == "both_coped" and source_id in tuple(primary_ids):
            raise ValueError(
                "The first selected tube is already one of this joint's mitered members. "
                "Select the diagonal/branch tube first. Mitered tubes are allowed as targets."
            )

    joint, by_id = _joint_context(document, node_xyz)
    needed = (source_id,) + tuple(target_ids)
    missing = [ident for ident in needed if ident not in by_id]
    if missing:
        raise ValueError(
            "One selected tube was not resolved as a member of this joint. "
            "Select the generated frame members themselves, not a layout line or joint marker."
        )

    coped_ends = []
    for target_id in target_ids:
        specification = build_cope_specification(
            CopeInstruction(
                joint=joint,
                coped_member=by_id[source_id],
                target_member=by_id[target_id],
            )
        )
        coped_ends.append(specification.coped_end)
    if len(set(coped_ends)) != 1:
        raise ValueError("The selected targets do not cut the same end of the source tube.")
    return node_key_value


def apply_selected_cope(
    document,
    selection,
):
    """Persist one direct cope plan and refresh bent targets in place."""

    selection = list(
        selection
        or ()
    )

    (
        node_xyz,
        source_id,
        target_ids,
    ) = selected_cope_request(
        selection
    )

    node_key_value = _preflight(
        document,
        node_xyz,
        source_id,
        target_ids,
    )

    current = load_joint_cope_pairs(
        document,
        node_key_value,
    )

    updated = replace_source_pairs(
        current,
        source_id,
        target_ids,
    )

    has_bent_target = any(
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
        for obj in selection[
            1:
        ]
    )

    started = False

    try:
        document.openTransaction(
            "Cope Selected ForgeCAD Member"
        )
        started = True

        replace_joint_cope_pairs(
            document,
            node_key_value,
            updated,
        )

        FreeCADGui.Selection.clearSelection()

        if has_bent_target:
            # A converted bent tube owns consumed layout members. Re-rendering
            # the layout here could recreate those consumed members as straight
            # tubes. Reapply fabrication against the existing mixed structural
            # model instead.
            from forgecad.adapters.freecad.fabrication_refresh import (
                refresh_fabrication_for_document,
            )

            refresh_fabrication_for_document(
                document
            )

        else:
            # Preserve the proven straight-member behavior.
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
        source_id,
        target_ids,
    )



class CopeSelectedCommand:
    def GetResources(self):
        return {
            "MenuText": "Cope Selected",
            "ToolTip": (
                "Select the tube to cope first, then one to three target tubes. "
                "Existing target miters are preserved."
            ),
        }

    def Activated(self):
        document = FreeCAD.ActiveDocument
        if document is None:
            _warn("Cope Selected", "Open a ForgeCAD project first.")
            return
        selection = list(FreeCADGui.Selection.getSelection())
        try:
            source_id, target_ids = apply_selected_cope(document, selection)
        except Exception as error:
            _warn("Cope Selected", error)
            return
        FreeCAD.Console.PrintMessage(
            "ForgeCAD: coped selected member to "
            + str(len(target_ids))
            + " target(s). Existing primary treatment was preserved.\n"
        )

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


def register_command():
    FreeCADGui.addCommand(COMMAND_NAME, CopeSelectedCommand())
