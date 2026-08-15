"""FreeCAD command for creating a parametric ForgeCAD bent tube."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.adapters.freecad.bender_library_store import (
    load_bender_library,
)
from forgecad.adapters.freecad.bent_tube_object import (
    create_bent_tube_object,
)
from forgecad.adapters.freecad.dialogs.create_bent_tube import (
    CreateBentTubeDialog,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)
from forgecad.services import (
    create_default_material,
    create_default_tube_library,
)
from forgecad.services.bent_tube_creation import (
    create_bent_tube,
)
from forgecad.services.bent_tube_tooling import (
    attach_tooling,
)


COMMAND_NAME = "ForgeCAD_CreateBentTube"


def create_tube_from_dialog(
    dialog,
):
    """Build a BentTube from dialog values."""

    library = create_default_tube_library()

    profile = library.get(
        dialog.profile_name
    )

    return create_bent_tube(
        dialog.definition,
        profile,
        create_default_material(),
    )


def resolve_dialog_tooling(
    dialog,
    bender_library,
):
    """Return selected project tooling or None."""

    tooling_name = dialog.tooling_name

    if tooling_name is None:
        return None

    return bender_library.get(
        tooling_name
    )


def ensure_tooling_properties(
    obj,
):
    """Ensure a bent-tube object can store tooling metadata."""

    if not hasattr(
        obj,
        "BenderTooling",
    ):
        obj.addProperty(
            "App::PropertyString",
            "BenderTooling",
            "ForgeCAD Bending",
        )

    if not hasattr(
        obj,
        "MachineCutLength",
    ):
        obj.addProperty(
            "App::PropertyLength",
            "MachineCutLength",
            "ForgeCAD Bending",
        )

    if not hasattr(
        obj,
        "MachineBendCount",
    ):
        obj.addProperty(
            "App::PropertyInteger",
            "MachineBendCount",
            "ForgeCAD Bending",
        )

    for property_name in (
        "BenderTooling",
        "MachineCutLength",
        "MachineBendCount",
    ):
        try:
            obj.setEditorMode(
                property_name,
                1,
            )
        except Exception:
            pass

    return obj


def store_tooling_result(
    obj,
    tooling_result,
):
    """Store selected tooling and summary instruction metadata."""

    ensure_tooling_properties(
        obj
    )

    if not tooling_result.has_tooling:
        obj.BenderTooling = ""
        obj.MachineCutLength = 0.0
        obj.MachineBendCount = 0
        return

    instructions = (
        tooling_result.machine_instructions()
    )

    obj.BenderTooling = (
        tooling_result.tooling.name
    )
    obj.MachineCutLength = (
        instructions.cut_length_mm
    )
    obj.MachineBendCount = (
        instructions.bend_count
    )


class CreateBentTubeCommand:
    """Create one editable physical bent tube."""

    def GetResources(
        self,
    ):
        return {
            "MenuText": "Create Bent Tube",
            "ToolTip": (
                "Create a continuous parametric tube "
                "containing one or more bends"
            ),
        }

    def Activated(
        self,
    ):
        document = FreeCAD.ActiveDocument

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Project",
                "Create or open a ForgeCAD project first.",
            )
            return

        bender_library = (
            load_bender_library(
                document
            )
        )

        dialog = CreateBentTubeDialog(
            tooling_names=(
                bender_library.names
            ),
            active_tooling_name=(
                bender_library.active_name
            ),
            parent=(
                FreeCADGui.getMainWindow()
            ),
        )

        if (
            dialog.exec_()
            != QtGui.QDialog.Accepted
        ):
            return

        try:
            tube = create_tube_from_dialog(
                dialog
            )

            tooling = resolve_dialog_tooling(
                dialog,
                bender_library,
            )

            tooling_result = attach_tooling(
                tube,
                tooling,
            )

            obj = create_bent_tube_object(
                document,
                tube,
            )

            obj.TubeName = (
                dialog.definition.name
            )

            store_tooling_result(
                obj,
                tooling_result,
            )

            tree = initialize_project_tree(
                document
            )

            tree[
                "Bent Tubes"
            ].addObject(
                obj
            )

            document.recompute()

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Cannot Create Bent Tube",
                str(
                    error
                ),
            )
            return

        try:
            obj.ViewObject.Visibility = True
        except Exception:
            pass

        FreeCADGui.activeDocument().activeView().fitAll()

    def IsActive(
        self,
    ):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Create Bent Tube command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        CreateBentTubeCommand(),
    )
