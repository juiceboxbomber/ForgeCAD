"""CSV export services for ForgeCAD tube stock plans."""

import csv
import io


def tube_stock_plan_to_csv(plan) -> str:
    """Return one ForgeCAD tube stock plan as shop-oriented CSV text."""

    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow(
        [
            "Tube Profile",
            "Material",
            "Stock Stick",
            "Cut Order",
            "Member",
            "Description",
            "Finished Cut Length (mm)",
            "Kerf Allowance (mm)",
            "Remaining Stock (mm)",
        ]
    )

    for profile in plan.profile_plans:
        for stick in profile.sticks:
            remaining = stick.stock_length_mm

            for cut_order, piece in enumerate(
                stick.pieces,
                start=1,
            ):
                remaining -= (
                    piece.length_mm
                    + stick.saw_kerf_mm
                )

                if abs(remaining) < 1e-9:
                    remaining = 0.0

                writer.writerow(
                    [
                        profile.tube_profile,
                        profile.material,
                        stick.stick_number,
                        cut_order,
                        piece.member_id,
                        piece.member_name,
                        f"{piece.length_mm:.3f}",
                        f"{stick.saw_kerf_mm:.3f}",
                        f"{remaining:.3f}",
                    ]
                )

    writer.writerow([])

    writer.writerow(
        [
            "Totals",
            "Sticks Purchased",
            "Finished Tube Length (mm)",
            "Kerf Loss (mm)",
            "Drop (mm)",
            "Purchased Stock Length (mm)",
        ]
    )

    writer.writerow(
        [
            "Totals",
            plan.stick_count,
            f"{plan.total_piece_length_mm:.3f}",
            f"{plan.total_kerf_loss_mm:.3f}",
            f"{plan.total_drop_length_mm:.3f}",
            f"{plan.total_stock_length_mm:.3f}",
        ]
    )

    return output.getvalue()
