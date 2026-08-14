"""FreeCAD command for creating a parametric ForgeCAD bent tube."""

import FreeCAD
import FreeCADGui
from PySide import QtGui

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

        dialog = CreateBentTubeDialog(
            FreeCADGui.getMainWindow(),
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

            obj = create_bent_tube_object(
                document,
                tube,
            )

            obj.TubeName = (
                dialog.definition.name
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
