"""FreeCAD dialog for ForgeCAD tube stock planning."""

from PySide import QtGui

from forgecad.services.tube_stock import (
    DEFAULT_SAW_KERF_MM,
    DEFAULT_STOCK_LENGTH_MM,
    plan_tube_stock,
)
from forgecad.services.tube_stock_export import (
    tube_stock_plan_to_csv,
)


class TubeStockPlanDialog(QtGui.QDialog):
    """Display a shop-oriented tube stock cutting plan."""

    def __init__(
        self,
        cut_list,
        parent=None,
    ):
        super().__init__(parent)

        self.cut_list = cut_list
        self.plan = None

        self.setWindowTitle(
            "ForgeCAD Tube Stock Plan"
        )

        self.setMinimumWidth(
            1100
        )
        self.setMinimumHeight(
            620
        )

        stock_label = QtGui.QLabel(
            "Stock Length"
        )

        self.stock_length = (
            QtGui.QDoubleSpinBox()
        )
        self.stock_length.setDecimals(
            1
        )
        self.stock_length.setRange(
            1.0,
            100000.0,
        )
        self.stock_length.setValue(
            DEFAULT_STOCK_LENGTH_MM
        )
        self.stock_length.setSuffix(
            " mm"
        )

        kerf_label = QtGui.QLabel(
            "Saw Kerf"
        )

        self.saw_kerf = (
            QtGui.QDoubleSpinBox()
        )
        self.saw_kerf.setDecimals(
            3
        )
        self.saw_kerf.setRange(
            0.0,
            100.0,
        )
        self.saw_kerf.setValue(
            DEFAULT_SAW_KERF_MM
        )
        self.saw_kerf.setSuffix(
            " mm"
        )

        recalculate_button = (
            QtGui.QPushButton(
                "Recalculate"
            )
        )
        recalculate_button.clicked.connect(
            self.recalculate
        )

        controls = QtGui.QHBoxLayout()
        controls.addWidget(
            stock_label
        )
        controls.addWidget(
            self.stock_length
        )
        controls.addSpacing(
            18
        )
        controls.addWidget(
            kerf_label
        )
        controls.addWidget(
            self.saw_kerf
        )
        controls.addSpacing(
            18
        )
        controls.addWidget(
            recalculate_button
        )
        controls.addStretch()

        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(
            7
        )
        self.table.setHorizontalHeaderLabels(
            [
                "Tube Profile",
                "Material",
                "Stick",
                "Piece",
                "Description",
                "Cut Length (mm)",
                "Remaining (mm)",
            ]
        )
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

        note = QtGui.QLabel(
            (
                "Stock is grouped by tube profile and material. "
                "Each piece consumes its finished length plus one "
                "saw-kerf allowance."
            )
        )
        note.setWordWrap(
            True
        )

        export_button = QtGui.QPushButton(
            "Export CSV"
        )
        export_button.clicked.connect(
            self.export_csv
        )

        close_button = QtGui.QPushButton(
            "Close"
        )
        close_button.clicked.connect(
            self.accept
        )

        buttons = QtGui.QHBoxLayout()
        buttons.addWidget(
            export_button
        )
        buttons.addStretch()
        buttons.addWidget(
            close_button
        )

        layout = QtGui.QVBoxLayout()
        layout.addLayout(
            controls
        )
        layout.addWidget(
            note
        )
        layout.addWidget(
            self.table
        )
        layout.addWidget(
            self.summary_label
        )
        layout.addLayout(
            buttons
        )

        self.setLayout(
            layout
        )

        self.recalculate()

    def recalculate(self):
        """Rebuild the stock plan from current settings."""

        try:
            self.plan = plan_tube_stock(
                self.cut_list,
                stock_length_mm=(
                    self.stock_length.value()
                ),
                saw_kerf_mm=(
                    self.saw_kerf.value()
                ),
            )
        except ValueError as error:
            QtGui.QMessageBox.warning(
                self,
                "Cannot Build Stock Plan",
                str(
                    error
                ),
            )
            return

        self.populate_table()
        self.update_summary()

    def populate_table(self):
        """Fill the cutting sequence table."""

        row_count = sum(
            stick.piece_count
            for profile
            in self.plan.profile_plans
            for stick
            in profile.sticks
        )

        self.table.setRowCount(
            row_count
        )

        row_index = 0

        for profile in (
            self.plan.profile_plans
        ):
            for stick in profile.sticks:
                remaining = (
                    stick.stock_length_mm
                )

                for piece in stick.pieces:
                    remaining -= (
                        piece.length_mm
                        + stick.saw_kerf_mm
                    )

                    if abs(
                        remaining
                    ) < 1e-9:
                        remaining = 0.0

                    values = [
                        profile.tube_profile,
                        profile.material,
                        str(
                            stick.stick_number
                        ),
                        piece.member_id,
                        piece.member_name,
                        (
                            f"{piece.length_mm:.2f}"
                        ),
                        (
                            f"{remaining:.2f}"
                        ),
                    ]

                    for (
                        column_index,
                        value,
                    ) in enumerate(
                        values
                    ):
                        self.table.setItem(
                            row_index,
                            column_index,
                            QtGui.QTableWidgetItem(
                                value
                            ),
                        )

                    row_index += 1

        self.table.resizeColumnsToContents()

    def export_csv(self):
        """Export the current stock plan to a CSV file."""

        if self.plan is None:
            self.recalculate()

        if self.plan is None:
            return

        default_name = (
            "ForgeCAD_stock_plan.csv"
        )

        try:
            import FreeCAD

            document = (
                FreeCAD.ActiveDocument
            )

            if document is not None:
                label = str(
                    getattr(
                        document,
                        "Label",
                        "",
                    )
                ).strip()

                if label:
                    default_name = (
                        f"{label}_stock_plan.csv"
                    )

        except ImportError:
            pass

        file_path, _ = (
            QtGui.QFileDialog.getSaveFileName(
                self,
                "Export ForgeCAD Tube Stock Plan",
                default_name,
                "CSV Files (*.csv)",
            )
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"

        csv_text = (
            tube_stock_plan_to_csv(
                self.plan
            )
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
                str(
                    error
                ),
            )
            return

        QtGui.QMessageBox.information(
            self,
            "Export Complete",
            (
                "ForgeCAD tube stock plan exported to:\n"
                f"{file_path}"
            ),
        )

    def update_summary(self):
        """Show overall stock requirements."""

        self.summary_label.setText(
            (
                f"Stock groups: {self.plan.profile_count}    "
                f"Sticks required: {self.plan.stick_count}    "
                f"Pieces: {self.plan.piece_count}    "
                f"Finished length: "
                f"{self.plan.total_piece_length_mm:.2f} mm    "
                f"Kerf loss: "
                f"{self.plan.total_kerf_loss_mm:.2f} mm    "
                f"Drop: "
                f"{self.plan.total_drop_length_mm:.2f} mm"
            )
        )
