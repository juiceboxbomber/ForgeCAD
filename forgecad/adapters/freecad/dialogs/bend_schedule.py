"""Bend Schedule dialog for ForgeCAD."""

from PySide import QtGui


class BendScheduleDialog(
    QtGui.QDialog
):
    """Display a shop-ready bend report."""

    HEADERS = (
        "Bend",
        "Mark Position (mm)",
        "Bend Angle (deg)",
        "CLR (mm)",
        "Rotation (deg)",
    )

    def __init__(
        self,
        report,
        tube_name="Bent Tube",
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.setWindowTitle(
            f"Bend Schedule - {tube_name}"
        )
        self.setMinimumWidth(
            760
        )

        self.summary_label = QtGui.QLabel(
            self._summary_text(
                report
            )
        )

        self.table = QtGui.QTableWidget(
            len(
                report.rows
            ),
            len(
                self.HEADERS
            ),
        )

        self.table.setHorizontalHeaderLabels(
            list(
                self.HEADERS
            )
        )

        for row_index, row in enumerate(
            report.rows
        ):
            values = (
                str(
                    row.bend_number
                ),
                f"{row.mark_position_mm:.3f}",
                f"{row.bend_angle_degrees:.3f}",
                f"{row.centerline_radius_mm:.3f}",
                f"{row.rotation_degrees:.3f}",
            )

            for column_index, value in enumerate(
                values
            ):
                self.table.setItem(
                    row_index,
                    column_index,
                    QtGui.QTableWidgetItem(
                        value
                    ),
                )

        try:
            self.table.resizeColumnsToContents()
        except Exception:
            pass

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Close
        )
        buttons.rejected.connect(
            self.reject
        )
        buttons.accepted.connect(
            self.accept
        )

        layout = QtGui.QVBoxLayout()
        layout.addWidget(
            self.summary_label
        )
        layout.addWidget(
            self.table
        )
        layout.addWidget(
            buttons
        )

        self.setLayout(
            layout
        )

    @staticmethod
    def _summary_text(
        report,
    ):
        """Return summary text for the schedule."""

        tooling = (
            report.tooling_name
            if report.tooling_name
            else "None"
        )

        return (
            f"Tooling: {tooling}\n"
            f"Bends: {report.bend_count}\n"
            f"Cut Length: {report.cut_length_mm:.3f} mm"
        )
