"""FreeCAD command for displaying a ForgeCAD fabrication cut list."""

import math

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.services import (
    create_default_material,
    create_default_tube_library,
)


COMMAND_NAME = "ForgeCAD_CutList"


def member_weight_kg(
    length_mm,
    outside_diameter_mm,
    wall_thickness_mm,
    density_kg_m3,
):
    """Calculate estimated weight for one hollow round tube."""

    inside_diameter_mm = (
        outside_diameter_mm
        - (2.0 * wall_thickness_mm)
    )

    outer_area = (
        math.pi
        / 4.0
        * outside_diameter_mm**2
    )

    inner_area = (
        math.pi
        / 4.0
        * inside_diameter_mm**2
    )

    cross_section_area_mm2 = (
        outer_area - inner_area
    )

    volume_m3 = (
        cross_section_area_mm2
        * length_mm
        / 1_000_000_000.0
    )

    return (
        volume_m3
        * density_kg_m3
    )


def frame_member_objects(document):
    """Return generated ForgeCAD members from the Frame group."""

    frame_group = document.getObject(
        "ForgeCADFrame"
    )

    if frame_group is None:
        return []

    members = []

    for obj in frame_group.Group:
        if not hasattr(
            obj,
            "MemberID",
        ):
            continue

        if not hasattr(
            obj,
            "TubeProfile",
        ):
            continue

        if not hasattr(
            obj,
            "MemberLength",
        ):
            continue

        members.append(
            obj
        )

    return members


def cut_list_rows(document):
    """Return fabrication data for generated FreeCAD members."""

    members = frame_member_objects(
        document
    )

    library = create_default_tube_library()
    default_material = create_default_material()

    rows = []

    for obj in members:
        profile_name = str(
            obj.TubeProfile
        )

        try:
            profile = library.get(
                profile_name
            )

            outside_diameter = (
                profile.outside_diameter
            )

            wall_thickness = (
                profile.wall_thickness
            )

        except KeyError:
            outside_diameter = float(
                obj.OutsideDiameter
            )

            wall_thickness = float(
                obj.WallThickness
            )

        length_mm = float(
            obj.MemberLength
        )

        material_name = getattr(
            obj,
            "Material",
            default_material.name,
        )

        weight_kg = member_weight_kg(
            length_mm=length_mm,
            outside_diameter_mm=outside_diameter,
            wall_thickness_mm=wall_thickness,
            density_kg_m3=default_material.density,
        )

        rows.append(
            {
                "member_id": str(
                    obj.MemberID
                ),
                "tube_profile": profile_name,
                "material": material_name,
                "length_mm": length_mm,
                "weight_kg": weight_kg,
            }
        )

    return rows


class CutListDialog(QtGui.QDialog):
    """Display the current ForgeCAD fabrication cut list."""

    def __init__(
        self,
        rows,
        parent=None,
    ):
        super().__init__(parent)

        self.rows = rows

        self.setWindowTitle(
            "ForgeCAD Cut List"
        )

        self.setMinimumWidth(
            760
        )

        self.setMinimumHeight(
            420
        )

        self.table = QtGui.QTableWidget()

        self.table.setColumnCount(
            5
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Member",
                "Tube Profile",
                "Material",
                "Length (mm)",
                "Weight (kg)",
            ]
        )

        self.table.setRowCount(
            len(rows)
        )

        self.populate_table()

        self.table.setEditTriggers(
            QtGui.QAbstractItemView.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows
        )

        header = (
            self.table.horizontalHeader()
        )

        header.setStretchLastSection(
            True
        )

        self.summary_label = (
            QtGui.QLabel()
        )

        self.update_summary()

        close_button = (
            QtGui.QPushButton(
                "Close"
            )
        )

        close_button.clicked.connect(
            self.accept
        )

        button_layout = (
            QtGui.QHBoxLayout()
        )

        button_layout.addStretch()
        button_layout.addWidget(
            close_button
        )

        layout = QtGui.QVBoxLayout()

        layout.addWidget(
            self.table
        )

        layout.addWidget(
            self.summary_label
        )

        layout.addLayout(
            button_layout
        )

        self.setLayout(
            layout
        )

    def populate_table(self):
        """Fill the cut-list table."""

        for row_index, row in enumerate(
            self.rows
        ):
            values = [
                row["member_id"],
                row["tube_profile"],
                row["material"],
                f'{row["length_mm"]:.2f}',
                f'{row["weight_kg"]:.3f}',
            ]

            for column_index, value in enumerate(
                values
            ):
                item = (
                    QtGui.QTableWidgetItem(
                        value
                    )
                )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.table.resizeColumnsToContents()

    def update_summary(self):
        """Show overall fabrication totals."""

        member_count = len(
            self.rows
        )

        total_length_mm = sum(
            row["length_mm"]
            for row in self.rows
        )

        total_weight_kg = sum(
            row["weight_kg"]
            for row in self.rows
        )

        self.summary_label.setText(
            (
                f"Members: {member_count}    "
                f"Total tube length: "
                f"{total_length_mm:.2f} mm    "
                f"Estimated weight: "
                f"{total_weight_kg:.3f} kg"
            )
        )


class CutListCommand:
    """Display a fabrication cut list for the active ForgeCAD frame."""

    def GetResources(self):
        return {
            "MenuText": "Cut List",
            "ToolTip": (
                "Display member lengths, tube profiles, "
                "materials, and estimated weights"
            ),
        }

    def Activated(self):
        document = FreeCAD.ActiveDocument

        if document is None:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Active Document",
                "Open or create a ForgeCAD project first.",
            )
            return

        rows = cut_list_rows(
            document
        )

        if not rows:
            QtGui.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "No Frame Members",
                (
                    "Generate the ForgeCAD frame before "
                    "creating a cut list."
                ),
            )
            return

        dialog = CutListDialog(
            rows,
            FreeCADGui.getMainWindow(),
        )

        dialog.exec_()

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument
            is not None
        )


def register_command() -> None:
    """Register the Cut List command."""

    FreeCADGui.addCommand(
        COMMAND_NAME,
        CutListCommand(),
    )
    