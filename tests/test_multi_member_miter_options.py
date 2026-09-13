"""Regression tests for explicit miter-pair options at multi-member joints."""

import sys
import types
from dataclasses import dataclass

fake_freecad = types.ModuleType("FreeCAD")
fake_part = types.ModuleType("Part")
fake_freecadgui = types.ModuleType("FreeCADGui")

sys.modules["FreeCAD"] = fake_freecad
sys.modules["Part"] = fake_part
sys.modules["FreeCADGui"] = fake_freecadgui

from forgecad.fabrication.joint_treatment import JointTreatmentMode
from forgecad.adapters.freecad.joint_treatment_options import (
    treatment_options_for_members,
)


@dataclass
class Vector:
    x: float
    y: float
    z: float


class FakeMember:
    def __init__(
        self,
        member_id,
        layout_id,
        end,
    ):
        self.MemberID = member_id
        self.MemberName = ""
        self.SourceLayoutID = layout_id
        self.StartPoint = Vector(0.0, 0.0, 0.0)
        self.EndPoint = end


def test_three_member_corner_offers_explicit_miter_pairs():
    first = FakeMember(
        "M001",
        "L001",
        Vector(500.0, 0.0, 0.0),
    )
    second = FakeMember(
        "M002",
        "L002",
        Vector(0.0, 500.0, 0.0),
    )
    upright = FakeMember(
        "M003",
        "L003",
        Vector(0.0, 0.0, 500.0),
    )

    options = treatment_options_for_members(
        [
            first,
            second,
            upright,
        ]
    )

    miter_options = [
        option
        for option in options
        if option.mode
        == JointTreatmentMode.BOTH_COPED
    ]

    assert {
        option.through_layout_ids
        for option in miter_options
    } == {
        ("L001", "L002"),
        ("L001", "L003"),
        ("L002", "L003"),
    }


def test_multi_member_miter_labels_identify_the_selected_pair():
    first = FakeMember(
        "M001",
        "L001",
        Vector(500.0, 0.0, 0.0),
    )
    second = FakeMember(
        "M002",
        "L002",
        Vector(0.0, 500.0, 0.0),
    )
    upright = FakeMember(
        "M003",
        "L003",
        Vector(0.0, 0.0, 500.0),
    )

    options = treatment_options_for_members(
        [
            first,
            second,
            upright,
        ]
    )

    labels = {
        option.label
        for option in options
        if option.mode
        == JointTreatmentMode.BOTH_COPED
    }

    assert "M001 + M002 Mitered" in labels
    assert "M001 + M003 Mitered" in labels
    assert "M002 + M003 Mitered" in labels
