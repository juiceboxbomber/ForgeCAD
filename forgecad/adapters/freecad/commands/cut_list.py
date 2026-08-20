"""FreeCAD command for displaying a ForgeCAD fabrication cut list."""

import math

import FreeCAD
import FreeCADGui
from PySide import QtGui

from forgecad.services import (
    CutList,
    CutListItem,
    cut_list_to_csv,
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

        member_name = str(
            getattr(
                obj,
                "MemberName",
                "",
            )
        ).strip()

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

        material_name = str(
            getattr(
                obj,
                "Material",
                default_material.name,
            )
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
                "member_name": member_name,
                "tube_profile": profile_name,
                "material": material_name,
                "length_mm": length_mm,
                "outside_diameter_mm": outside_diameter,
                "wall_thickness_mm": wall_thickness,
                "weight_kg": weight_kg,
            }
        )

    return rows


def cut_list_from_rows(rows):
    """Convert FreeCAD row data into the pure-Python CutList model."""

    items = []

    for row in rows:
        items.append(
            CutListItem(
                member_id=row[
                    "member_id"
                ],
                member_name=row[
                    "member_name"
                ],
                tube_profile=row[
                    "tube_profile"
                ],
                material=row[
                    "material"
                ],
                length_mm=row[
                    "length_mm"
                ],
                outside_diameter_mm=row[
                    "outside_diameter_mm"
                ],
                wall_thickness_mm=row[
                    "wall_thickness_mm"
                ],
                weight_kg=row[
                    "weight_kg"
                ],
            )
        )

    return CutList(
        items=items
    )


class CutListDialog(QtGui.QDialog):
    """Display the current ForgeCAD fabrication cut list."""

    def __init__(
        self,
        rows,
        parent=None,
    ):
        super().__init__(parent)

        self.rows = rows

        self.cut_list = cut_list_from_rows(
            rows
        )

        self.setWindowTitle(
            "ForgeCAD Cut List"
        )

        self.setMinimumWidth(
            940
        )

        self.setMinimumHeight(
            560
        )

        # -----------------------------------------------------
        # Member table
        # -----------------------------------------------------

        member_label = QtGui.QLabel(
            "Member Cut List"
        )

        self.table = QtGui.QTableWidget()

        self.table.setColumnCount(
            6
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Member",
                "Description",
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

        member_header = (
            self.table.horizontalHeader()
        )

        member_header.setStretchLastSection(
            True
        )

        # -----------------------------------------------------
        # Tube summary table
        # -----------------------------------------------------

        summary_title = QtGui.QLabel(
            "Tube Summary"
        )

        self.summary_table = (
            QtGui.QTableWidget()
        )

        self.summary_table.setColumnCount(
            4
        )

        self.summary_table.setHorizontalHeaderLabels(
            [
                "Tube Profile",
                "Pieces",
                "Total Length (mm)",
                "Total Weight (kg)",
            ]
        )

        tube_summary = (
            self.cut_list.summary_by_profile()
        )

        self.summary_table.setRowCount(
            len(tube_summary)
        )

        self.populate_summary_table(
            tube_summary
        )

        self.summary_table.setEditTriggers(
            QtGui.QAbstractItemView.NoEditTriggers
        )

        self.summary_table.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows
        )

        summary_header = (
            self.summary_table.horizontalHeader()
        )

        summary_header.setStretchLastSection(
            True
        )

        # -----------------------------------------------------
        # Overall totals
        # -----------------------------------------------------

        self.summary_label = (
            QtGui.QLabel()
        )

        self.update_summary()

        # -----------------------------------------------------
        # Buttons
        # -----------------------------------------------------

        export_button = (
            QtGui.QPushButton(
                "Export CSV"
            )
        )

        export_button.clicked.connect(
            self.export_csv
        )

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

        button_layout.addWidget(
            export_button
        )

        button_layout.addStretch()

        button_layout.addWidget(
            close_button
        )

        # -----------------------------------------------------
        # Main layout
        # -----------------------------------------------------

        layout = QtGui.QVBoxLayout()

        layout.addWidget(
            member_label
        )

        layout.addWidget(
            self.table
        )

        layout.addWidget(
            summary_title
        )

        layout.addWidget(
            self.summary_table
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
        """Fill the member cut-list table."""

        for row_index, row in enumerate(
            self.rows
        ):
            values = [
                row["member_id"],
                row["member_name"],
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

    def populate_summary_table(
        self,
        summary_items,
    ):
        """Fill the grouped tube summary table."""

        for row_index, summary in enumerate(
            summary_items
        ):
            values = [
                summary.tube_profile,
                str(
                    summary.piece_count
                ),
                (
                    f"{summary.total_length_mm:.2f}"
                ),
                (
                    f"{summary.total_weight_kg:.3f}"
                ),
            ]

            for column_index, value in enumerate(
                values
            ):
                item = (
                    QtGui.QTableWidgetItem(
                        value
                    )
                )

                self.summary_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.summary_table.resizeColumnsToContents()

    def update_summary(self):
        """Show overall fabrication totals."""

        self.summary_label.setText(
            (
                f"Members: "
                f"{self.cut_list.member_count}    "
                f"Total tube length: "
                f"{self.cut_list.total_length_mm:.2f} mm    "
                f"Estimated weight: "
                f"{self.cut_list.total_weight_kg:.3f} kg"
            )
        )

    def export_csv(self):
        """Export the displayed cut list to a CSV file."""

        document = FreeCAD.ActiveDocument

        if document is not None:
            default_name = (
                f"{document.Label}_cut_list.csv"
            )
        else:
            default_name = (
                "ForgeCAD_cut_list.csv"
            )

        file_path, _ = (
            QtGui.QFileDialog.getSaveFileName(
                self,
                "Export ForgeCAD Cut List",
                default_name,
                "CSV Files (*.csv)",
            )
        )

        if not file_path:
            return

        if not file_path.lower().endswith(
            ".csv"
        ):
            file_path += ".csv"

        csv_text = cut_list_to_csv(
            self.cut_list
        )

        try:
            with open(
                file_path,
                "w",
                encoding="utf-8",
                newline="",
            ) as output_file:
                output_file.write(
                    csv_text
                )

        except OSError as error:
            QtGui.QMessageBox.critical(
                self,
                "Export Failed",
                str(error),
            )
            return

        QtGui.QMessageBox.information(
            self,
            "Export Complete",
            (
                "ForgeCAD cut list exported to:\n"
                f"{file_path}"
            ),
        )


class CutListCommand:
    """Display a fabrication cut list for the active ForgeCAD frame."""

    def GetResources(self):
        return {
            "MenuText": "Cut List",
            "ToolTip": (
                "Display member names, lengths, tube profiles, "
                "material totals, and estimated weights"
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
    