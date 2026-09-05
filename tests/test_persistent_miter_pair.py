"""Regression tests for persistent Both Mitered member identity."""

import sys
import types
from types import SimpleNamespace


# Minimal FreeCAD / Part stubs required by the FreeCAD adapter package.
fake_freecad = types.ModuleType("FreeCAD")
fake_part = types.ModuleType("Part")
fake_freecadgui = types.ModuleType("FreeCADGui")

sys.modules["FreeCAD"] = fake_freecad
sys.modules["Part"] = fake_part
sys.modules["FreeCADGui"] = fake_freecadgui


from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatment,
)
from forgecad.adapters.freecad.joint_treatment_options import (
    both_mitered_option,
)
from forgecad.services.joint_extension import (
    extension_specifications_for_treatment,
)
from forgecad.services.joint_miter import (
    miter_specifications_for_treatment,
)


MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)

PROFILE = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)


def make_member(start, end):
    return Member(
        start=start,
        end=end,
        profile=PROFILE,
        material=MATERIAL,
    )


def make_three_member_corner():
    center = Node(0, 0, 0)

    first = make_member(
        center,
        Node(500, 0, 0),
    )

    second = make_member(
        center,
        Node(0, 500, 0),
    )

    upright = make_member(
        center,
        Node(0, 0, 500),
    )

    joint = Joint(
        node=center,
        members=[
            first,
            second,
            upright,
        ],
    )

    return joint, first, second, upright


def test_both_mitered_option_persists_pair_layout_ids():
    first = SimpleNamespace(SourceLayoutID="L001")
    second = SimpleNamespace(SourceLayoutID="L002")

    option = both_mitered_option(first, second)

    assert option.through_layout_ids == (
        "L001",
        "L002",
    )


def test_three_member_joint_miters_only_selected_pair():
    joint, first, second, upright = make_three_member_corner()

    treatment = JointTreatment.both_coped(
        joint,
        first,
        second,
    )

    specifications = miter_specifications_for_treatment(
        treatment
    )

    assert {
        specification.member
        for specification in specifications
    } == {
        first,
        second,
    }

    assert all(
        specification.member is not upright
        for specification in specifications
    )


def test_three_member_joint_extends_only_selected_miter_pair():
    joint, first, second, upright = make_three_member_corner()

    treatment = JointTreatment.both_coped(
        joint,
        first,
        second,
    )

    specifications = extension_specifications_for_treatment(
        treatment
    )

    assert {
        specification.member
        for specification in specifications
    } == {
        first,
        second,
    }

    assert all(
        specification.member is not upright
        for specification in specifications
    )
