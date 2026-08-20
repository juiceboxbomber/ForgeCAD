"""Tests for the FreeCAD joint-treatment resolver adapter."""

import sys
import types


fake_freecad = types.ModuleType(
    "FreeCAD"
)

fake_freecadgui = types.ModuleType(
    "FreeCADGui"
)

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = fake_freecad

sys.modules[
    "FreeCADGui"
] = fake_freecadgui

sys.modules[
    "Part"
] = fake_part


from forgecad.fabrication import (
    Joint,
    Material,
    Member,
    Node,
    TubeProfile,
)
from forgecad.adapters.freecad.joint_treatment_resolver_adapter import (
    connected_member_records,
    through_members_from_layout_ids,
)
from forgecad.adapters.freecad import (
    joint_treatment_resolver_adapter,
)
from forgecad.fabrication.joint_treatment import (
    JointTreatmentMode,
)


MATERIAL = Material(
    name="DOM",
    density=7850.0,
    yield_strength=350.0,
)


def make_profile():
    return TubeProfile(
        outside_diameter=44.45,
        wall_thickness=3.05,
    )


def make_member(
    start,
    end,
):
    return Member(
        start=start,
        end=end,
        profile=make_profile(),
        material=MATERIAL,
    )


class FakeMemberObject:
    """Minimal generated FreeCAD member identity."""

    def __init__(
        self,
        source_layout_id,
    ):
        self.SourceLayoutID = (
            source_layout_id
        )


def test_connected_member_records_filters_by_joint():
    joint_node = Node(
        0,
        0,
        0,
    )

    connected = make_member(
        joint_node,
        Node(
            100,
            0,
            0,
        ),
    )

    disconnected = make_member(
        Node(
            500,
            0,
            0,
        ),
        Node(
            600,
            0,
            0,
        ),
    )

    records = (
        (
            FakeMemberObject(
                "L001"
            ),
            connected,
        ),
        (
            FakeMemberObject(
                "L002"
            ),
            disconnected,
        ),
    )

    joint = Joint(
        node=joint_node,
        members=[
            connected,
        ],
    )

    result = connected_member_records(
        records,
        joint,
    )

    assert len(
        result
    ) == 1

    assert (
        result[0][1]
        is connected
    )


def test_through_member_resolves_from_layout_id():
    first = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            100,
            0,
            0,
        ),
    )

    second = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            0,
            100,
            0,
        ),
    )

    records = (
        (
            FakeMemberObject(
                "L001"
            ),
            first,
        ),
        (
            FakeMemberObject(
                "L002"
            ),
            second,
        ),
    )

    result = (
        through_members_from_layout_ids(
            records,
            (
                "L002",
            ),
        )
    )

    assert result == (
        second,
    )


def test_through_pair_preserves_saved_order():
    first = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            100,
            0,
            0,
        ),
    )

    second = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            0,
            100,
            0,
        ),
    )

    records = (
        (
            FakeMemberObject(
                "L001"
            ),
            first,
        ),
        (
            FakeMemberObject(
                "L002"
            ),
            second,
        ),
    )

    result = (
        through_members_from_layout_ids(
            records,
            (
                "L002",
                "L001",
            ),
        )
    )

    assert result == (
        second,
        first,
    )


def test_unknown_layout_id_is_not_resolved():
    member = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            100,
            0,
            0,
        ),
    )

    records = (
        (
            FakeMemberObject(
                "L001"
            ),
            member,
        ),
    )

    result = (
        through_members_from_layout_ids(
            records,
            (
                "DOES_NOT_EXIST",
            ),
        )
    )

    assert result == ()


def test_empty_layout_ids_returns_empty_tuple():
    member = make_member(
        Node(
            0,
            0,
            0,
        ),
        Node(
            100,
            0,
            0,
        ),
    )

    records = (
        (
            FakeMemberObject(
                "L001"
            ),
            member,
        ),
    )

    result = (
        through_members_from_layout_ids(
            records,
            (),
        )
    )

    assert result == ()

    
def test_treatment_uses_same_member_instances(
    monkeypatch,
):
    joint_node = Node(
        0,
        0,
        0,
    )

    first = make_member(
        joint_node,
        Node(
            100,
            0,
            0,
        ),
    )

    second = make_member(
        joint_node,
        Node(
            0,
            100,
            0,
        ),
    )

    records = (
        (
            FakeMemberObject(
                "L001"
            ),
            first,
        ),
        (
            FakeMemberObject(
                "L002"
            ),
            second,
        ),
    )

    original_joint = Joint(
        node=joint_node,
        members=[
            first,
            second,
        ],
    )

    monkeypatch.setattr(
        joint_treatment_resolver_adapter,
        "load_joint_treatment",
        lambda document, key: (
            "member_through",
            (
                "L001",
            ),
        ),
    )

    treatment = (
        joint_treatment_resolver_adapter
        .treatment_for_joint(
            object(),
            original_joint,
            records,
        )
    )

    assert (
        treatment.mode
        == JointTreatmentMode.MEMBER_THROUGH
    )

    assert len(
        treatment.through_members
    ) == 1

    assert (
        treatment.through_members[
            0
        ]
        is treatment.joint.members[
            0
        ]
    )
    