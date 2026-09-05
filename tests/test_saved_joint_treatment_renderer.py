"""Tests for rebuilding saved joint treatments in the FreeCAD renderer."""

import sys
import types


# ---------------------------------------------------------
# Minimal FreeCAD / Part stubs
# ---------------------------------------------------------

fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_part = types.ModuleType(
    "Part"
)

fake_freecadgui = types.ModuleType(
    "FreeCADGui"
)

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "Part"
] = fake_part

sys.modules[
    "FreeCADGui"
] = fake_freecadgui


from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatmentMode,
)
from forgecad.adapters.freecad.renderer import (
    member_for_layout_id,
    saved_treatment_for_joint,
)


PROFILE = TubeProfile(
    outside_diameter=44.45,
    wall_thickness=3.048,
)

MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


def make_member(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=PROFILE,
        material=MATERIAL,
    )


def make_corner():
    center = Node(
        0,
        0,
        0,
    )

    first = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    second = make_member(
        center,
        Node(
            0,
            500,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            first,
            second,
        ],
    )

    return (
        joint,
        first,
        second,
    )


def make_t_joint():
    center = Node(
        0,
        0,
        0,
    )

    left = make_member(
        center,
        Node(
            -500,
            0,
            0,
        ),
    )

    right = make_member(
        center,
        Node(
            500,
            0,
            0,
        ),
    )

    branch = make_member(
        center,
        Node(
            0,
            500,
            0,
        ),
    )

    joint = Joint(
        node=center,
        members=[
            left,
            right,
            branch,
        ],
    )

    return (
        joint,
        left,
        right,
        branch,
    )


class FakeTreatmentObject:
    def __init__(
        self,
        node_key,
        mode,
        through_layout_ids="",
    ):
        self.NodeKey = (
            node_key
        )

        self.TreatmentMode = (
            mode
        )

        self.ThroughLayoutIDs = (
            through_layout_ids
        )


class FakeTreatmentGroup:
    def __init__(
        self,
        objects,
    ):
        self.Group = list(
            objects
        )


class FakeDocument:
    def __init__(
        self,
        treatment_objects=None,
    ):
        self.treatment_group = (
            FakeTreatmentGroup(
                treatment_objects
                or []
            )
        )

    def getObject(
        self,
        name,
    ):
        if (
            name
            == "ForgeCADJointTreatments"
        ):
            return (
                self.treatment_group
            )

        if (
            name
            == "ForgeCADProject"
        ):
            return None

        return None

    def addObject(
        self,
        type_name,
        name,
    ):
        raise AssertionError(
            "Test should not create "
            "document objects."
        )

    def recompute(
        self,
    ):
        pass


def test_member_for_layout_id_returns_matching_joint_member():
    joint, first, second = (
        make_corner()
    )

    mapping = {
        id(first): "L001",
        id(second): "L002",
    }

    assert (
        member_for_layout_id(
            joint,
            "L002",
            mapping,
        )
        is second
    )


def test_member_for_layout_id_returns_none_when_missing():
    joint, first, second = (
        make_corner()
    )

    mapping = {
        id(first): "L001",
        id(second): "L002",
    }

    assert (
        member_for_layout_id(
            joint,
            "L999",
            mapping,
        )
        is None
    )


def test_missing_saved_treatment_falls_back_to_auto():
    joint, first, second = (
        make_corner()
    )

    document = FakeDocument()

    mapping = {
        id(first): "L001",
        id(second): "L002",
    }

    treatment = (
        saved_treatment_for_joint(
            document,
            joint,
            mapping,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.AUTO
    )


def test_saved_auto_treatment_loads_as_auto():
    joint, first, second = (
        make_corner()
    )

    document = FakeDocument(
        [
            FakeTreatmentObject(
                "0.000000,0.000000,0.000000",
                "auto",
            )
        ]
    )

    mapping = {
        id(first): "L001",
        id(second): "L002",
    }

    treatment = (
        saved_treatment_for_joint(
            document,
            joint,
            mapping,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.AUTO
    )


def test_saved_member_through_resolves_member():
    joint, first, second = (
        make_corner()
    )

    document = FakeDocument(
        [
            FakeTreatmentObject(
                "0.000000,0.000000,0.000000",
                "member_through",
                "L002",
            )
        ]
    )

    mapping = {
        id(first): "L001",
        id(second): "L002",
    }

    treatment = (
        saved_treatment_for_joint(
            document,
            joint,
            mapping,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.MEMBER_THROUGH
    )

    assert treatment.through_members == (
        second,
    )


def test_saved_both_coped_loads_for_corner():
    joint, first, second = (
        make_corner()
    )

    document = FakeDocument(
        [
            FakeTreatmentObject(
                "0.000000,0.000000,0.000000",
                "both_coped",
            )
        ]
    )

    mapping = {
        id(first): "L001",
        id(second): "L002",
    }

    treatment = (
        saved_treatment_for_joint(
            document,
            joint,
            mapping,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.BOTH_COPED
    )


def test_saved_through_pair_resolves_two_members():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    document = FakeDocument(
        [
            FakeTreatmentObject(
                "0.000000,0.000000,0.000000",
                "through_pair",
                "L001|L002",
            )
        ]
    )

    mapping = {
        id(left): "L001",
        id(right): "L002",
        id(branch): "L003",
    }

    treatment = (
        saved_treatment_for_joint(
            document,
            joint,
            mapping,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.THROUGH_PAIR
    )

    assert treatment.through_members == (
        left,
        right,
    )


def test_stale_member_through_layout_id_falls_back_to_auto():
    joint, first, second = (
        make_corner()
    )

    document = FakeDocument(
        [
            FakeTreatmentObject(
                "0.000000,0.000000,0.000000",
                "member_through",
                "L999",
            )
        ]
    )

    mapping = {
        id(first): "L001",
        id(second): "L002",
    }

    treatment = (
        saved_treatment_for_joint(
            document,
            joint,
            mapping,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.AUTO
    )


def test_stale_through_pair_layout_id_falls_back_to_auto():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    document = FakeDocument(
        [
            FakeTreatmentObject(
                "0.000000,0.000000,0.000000",
                "through_pair",
                "L001|L999",
            )
        ]
    )

    mapping = {
        id(left): "L001",
        id(right): "L002",
        id(branch): "L003",
    }

    treatment = (
        saved_treatment_for_joint(
            document,
            joint,
            mapping,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.AUTO
    )


def test_unknown_mode_falls_back_to_auto():
    joint, first, second = (
        make_corner()
    )

    document = FakeDocument(
        [
            FakeTreatmentObject(
                "0.000000,0.000000,0.000000",
                "nonsense_mode",
            )
        ]
    )

    mapping = {
        id(first): "L001",
        id(second): "L002",
    }

    treatment = (
        saved_treatment_for_joint(
            document,
            joint,
            mapping,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.AUTO
    )


def test_saved_both_coped_pair_survives_additional_member():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    document = FakeDocument(
        [
            FakeTreatmentObject(
                "0.000000,0.000000,0.000000",
                "both_coped",
                "L001|L003",
            )
        ]
    )

    mapping = {
        id(left): "L001",
        id(right): "L002",
        id(branch): "L003",
    }

    treatment = saved_treatment_for_joint(
        document,
        joint,
        mapping,
    )

    assert treatment.mode == JointTreatmentMode.BOTH_COPED
    assert treatment.through_members == (
        left,
        branch,
    )


def test_legacy_both_coped_without_pair_is_ambiguous_after_member_added():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    document = FakeDocument(
        [
            FakeTreatmentObject(
                "0.000000,0.000000,0.000000",
                "both_coped",
            )
        ]
    )

    mapping = {
        id(left): "L001",
        id(right): "L002",
        id(branch): "L003",
    }

    treatment = saved_treatment_for_joint(
        document,
        joint,
        mapping,
    )

    assert treatment.mode == JointTreatmentMode.AUTO


def test_stale_both_coped_pair_falls_back_to_auto():
    (
        joint,
        left,
        right,
        branch,
    ) = make_t_joint()

    document = FakeDocument(
        [
            FakeTreatmentObject(
                "0.000000,0.000000,0.000000",
                "both_coped",
                "L001|L999",
            )
        ]
    )

    mapping = {
        id(left): "L001",
        id(right): "L002",
        id(branch): "L003",
    }

    treatment = saved_treatment_for_joint(
        document,
        joint,
        mapping,
    )

    assert treatment.mode == JointTreatmentMode.AUTO
