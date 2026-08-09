"""Fabrication cut-list services for ForgeCAD."""

import csv
import io
from dataclasses import dataclass, field

from forgecad.fabrication import Frame, Member
from forgecad.services.project_service import (
    create_default_tube_library,
)


@dataclass(frozen=True, slots=True)
class CutListItem:
    """One fabricated tube in a ForgeCAD cut list."""

    member_id: str
    tube_profile: str
    material: str
    length_mm: float
    outside_diameter_mm: float
    wall_thickness_mm: float
    weight_kg: float


@dataclass(frozen=True, slots=True)
class TubeSummaryItem:
    """Grouped fabrication totals for one tube profile."""

    tube_profile: str
    piece_count: int
    total_length_mm: float
    total_weight_kg: float


@dataclass(slots=True)
class CutList:
    """Collection of fabricated tube members."""

    items: list[CutListItem] = field(
        default_factory=list
    )

    @property
    def member_count(self) -> int:
        """Return the number of cut-list items."""

        return len(self.items)

    @property
    def total_length_mm(self) -> float:
        """Return total tube length in millimeters."""

        return sum(
            item.length_mm
            for item in self.items
        )

    @property
    def total_weight_kg(self) -> float:
        """Return estimated total tube weight."""

        return sum(
            item.weight_kg
            for item in self.items
        )

    def length_by_profile(
        self,
    ) -> dict[str, float]:
        """Return total required length for each tube profile."""

        totals: dict[str, float] = {}

        for item in self.items:
            totals[item.tube_profile] = (
                totals.get(
                    item.tube_profile,
                    0.0,
                )
                + item.length_mm
            )

        return totals

    def count_by_profile(
        self,
    ) -> dict[str, int]:
        """Return member quantity for each tube profile."""

        counts: dict[str, int] = {}

        for item in self.items:
            counts[item.tube_profile] = (
                counts.get(
                    item.tube_profile,
                    0,
                )
                + 1
            )

        return counts

    def summary_by_profile(
        self,
    ) -> list[TubeSummaryItem]:
        """Return grouped fabrication totals by tube profile."""

        grouped = {}

        for item in self.items:
            profile_name = item.tube_profile

            if profile_name not in grouped:
                grouped[profile_name] = {
                    "piece_count": 0,
                    "total_length_mm": 0.0,
                    "total_weight_kg": 0.0,
                }

            grouped[profile_name][
                "piece_count"
            ] += 1

            grouped[profile_name][
                "total_length_mm"
            ] += item.length_mm

            grouped[profile_name][
                "total_weight_kg"
            ] += item.weight_kg

        return [
            TubeSummaryItem(
                tube_profile=profile_name,
                piece_count=values[
                    "piece_count"
                ],
                total_length_mm=values[
                    "total_length_mm"
                ],
                total_weight_kg=values[
                    "total_weight_kg"
                ],
            )
            for profile_name, values
            in grouped.items()
        ]


def profile_name_for_member(
    member: Member,
) -> str:
    """Return the standard library name matching a member profile."""

    library = create_default_tube_library()

    for name in library.names:
        if library.get(name) == member.profile:
            return name

    return (
        f"{member.profile.outside_diameter:.3f} x "
        f"{member.profile.wall_thickness:.3f} mm"
    )


def member_weight_kg(
    member: Member,
) -> float:
    """Return estimated tube weight in kilograms."""

    # Tube profile area is stored in mm².
    #
    # area_mm2 * length_mm = volume_mm3
    #
    # 1 m³ = 1,000,000,000 mm³
    volume_m3 = (
        member.profile.cross_sectional_area
        * member.length
        / 1_000_000_000.0
    )

    return (
        volume_m3
        * member.material.density
    )


def cut_list_item_from_member(
    member: Member,
    member_id: str,
) -> CutListItem:
    """Create one fabrication cut-list entry."""

    return CutListItem(
        member_id=member_id,
        tube_profile=profile_name_for_member(
            member
        ),
        material=member.material.name,
        length_mm=member.length,
        outside_diameter_mm=(
            member.profile.outside_diameter
        ),
        wall_thickness_mm=(
            member.profile.wall_thickness
        ),
        weight_kg=member_weight_kg(
            member
        ),
    )


def build_cut_list(
    frame: Frame,
) -> CutList:
    """Build a fabrication cut list from a ForgeCAD frame."""

    items = []

    for index, member in enumerate(
        frame.members,
        start=1,
    ):
        items.append(
            cut_list_item_from_member(
                member,
                member_id=f"M{index:03d}",
            )
        )

    return CutList(
        items=items
    )


def cut_list_to_csv(
    cut_list: CutList,
) -> str:
    """Return a ForgeCAD cut list as CSV text."""

    output = io.StringIO(
        newline=""
    )

    writer = csv.writer(
        output
    )

    writer.writerow(
        [
            "Member",
            "Tube Profile",
            "Material",
            "Length (mm)",
            "Outside Diameter (mm)",
            "Wall Thickness (mm)",
            "Weight (kg)",
        ]
    )

    for item in cut_list.items:
        writer.writerow(
            [
                item.member_id,
                item.tube_profile,
                item.material,
                f"{item.length_mm:.3f}",
                f"{item.outside_diameter_mm:.3f}",
                f"{item.wall_thickness_mm:.3f}",
                f"{item.weight_kg:.6f}",
            ]
        )

    writer.writerow([])

    writer.writerow(
        [
            "Tube Summary",
            "Pieces",
            "Total Length (mm)",
            "Total Weight (kg)",
        ]
    )

    for summary in cut_list.summary_by_profile():
        writer.writerow(
            [
                summary.tube_profile,
                summary.piece_count,
                f"{summary.total_length_mm:.3f}",
                f"{summary.total_weight_kg:.6f}",
            ]
        )

    writer.writerow([])

    writer.writerow(
        [
            "Totals",
            cut_list.member_count,
            f"{cut_list.total_length_mm:.3f}",
            f"{cut_list.total_weight_kg:.6f}",
        ]
    )

    return output.getvalue()
