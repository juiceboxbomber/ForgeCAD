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
from forgecad.adapters.freecad.commands.generate_nodes import (
    SOURCE_MANUAL,
    create_node_object,
    next_node_id,
    node_by_point,
)
from forgecad.adapters.freecad.dialogs.create_bent_tube import (
    CreateBentTubeDialog,
)
from forgecad.adapters.freecad.document_tree import (
    initialize_project_tree,
)
from forgecad.geometry import (
    Point3D,
    Vector3D,
)
from forgecad.services import (
    create_default_material,
    create_default_tube_library,
)
from forgecad.services.bent_tube_creation import (
    create_bent_tube,
)
from forgecad.services.bent_tube_path import (
    build_bent_tube_centerline,
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


def _point3d_from_vector(
    vector,
) -> Point3D:
    """Convert a FreeCAD vector-like value to Point3D."""

    return Point3D(
        float(
            vector.x
        ),
        float(
            vector.y
        ),
        float(
            vector.z
        ),
    )


def _vector3d_from_vector(
    vector,
) -> Vector3D:
    """Convert a FreeCAD vector-like value to Vector3D."""

    return Vector3D(
        float(
            vector.x
        ),
        float(
            vector.y
        ),
        float(
            vector.z
        ),
    )


def solved_bent_tube_endpoints(
    obj,
):
    """Return the true solved start and end points for a bent-tube object."""

    proxy = getattr(
        obj,
        "Proxy",
        None,
    )

    if (
        proxy is None
        or not hasattr(
            proxy,
            "_tube_from_properties",
        )
    ):
        raise ValueError(
            "Object is not a ForgeCAD bent tube."
        )

    tube = proxy._tube_from_properties(
        obj
    )

    centerline = build_bent_tube_centerline(
        tube,
        start_point=_point3d_from_vector(
            obj.StartPoint
        ),
        initial_direction=_vector3d_from_vector(
            obj.InitialDirection
        ),
        initial_bend_normal=_vector3d_from_vector(
            obj.InitialBendNormal
        ),
    )

    start = FreeCAD.Vector(
        centerline.start_point.x,
        centerline.start_point.y,
        centerline.start_point.z,
    )

    end = FreeCAD.Vector(
        centerline.end_point.x,
        centerline.end_point.y,
        centerline.end_point.z,
    )

    return (
        start,
        end,
    )


def ensure_node_at_point(
    document,
    nodes_group,
    point,
):
    """Return an existing ForgeCAD node at point or create one."""

    existing = node_by_point(
        nodes_group,
        point,
    )

    if existing is not None:
        return existing

    node_id = next_node_id(
        nodes_group
    )

    node_object = create_node_object(
        document,
        point,
        node_id,
        source_type=SOURCE_MANUAL,
    )

    nodes_group.addObject(
        node_object
    )

    return node_object


def ensure_bent_tube_endpoint_nodes(
    document,
    obj,
):
    """
    Create or reuse structural nodes at the true bent-tube endpoints.

    The node positions are taken from the solved centerline rather than
    from a straight chord between the tube ends.
    """

    tree = initialize_project_tree(
        document
    )

    nodes_group = tree[
        "Nodes"
    ]

    start_point, end_point = (
        solved_bent_tube_endpoints(
            obj
        )
    )

    start_node = ensure_node_at_point(
        document,
        nodes_group,
        start_point,
    )

    end_node = ensure_node_at_point(
        document,
        nodes_group,
        end_point,
    )

    document.recompute()

    return (
        start_node,
        end_node,
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

            ensure_bent_tube_endpoint_nodes(
                document,
                obj,
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
