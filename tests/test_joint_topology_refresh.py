"""Tests for the shared ForgeCAD topology-refresh hook."""

import importlib
import sys
import types


fake_freecad = types.ModuleType(
    "FreeCAD"
)

sys.modules[
    "FreeCAD"
] = fake_freecad


fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "Part"
] = fake_part


module = importlib.import_module(
    "forgecad.adapters.freecad.topology_refresh"
)


class FakeItem:
    def __init__(
        self,
        node_key,
        joint,
    ):
        self.node_key = node_key
        self.joint = joint


class FakeReview:
    def __init__(
        self,
        joints,
    ):
        self.joints = tuple(
            joints
        )


class FakeConstraintObject:
    def __init__(
        self,
        node_key,
    ):
        self.NodeKey = node_key


def install_fake_module(
    name,
    **attributes,
):
    fake = types.ModuleType(
        name
    )

    for key, value in attributes.items():
        setattr(
            fake,
            key,
            value,
        )

    original = sys.modules.get(
        name
    )

    sys.modules[
        name
    ] = fake

    return original


def restore_module(
    name,
    original,
):
    if original is None:
        sys.modules.pop(
            name,
            None,
        )
    else:
        sys.modules[
            name
        ] = original


def test_refresh_joint_topology_returns_empty_for_no_document():
    assert module.refresh_joint_topology(
        None
    ) == (
        (),
        (),
    )


def test_synchronize_saves_current_constraints_and_removes_stale_records():
    document = object()

    joint_a = object()
    joint_b = object()

    review = FakeReview(
        [
            FakeItem(
                "A",
                joint_a,
            ),
            FakeItem(
                "B",
                joint_b,
            ),
        ]
    )

    constraint_a = object()

    existing = [
        FakeConstraintObject(
            "A"
        ),
        FakeConstraintObject(
            "STALE"
        ),
    ]

    saved = []
    removed = []

    originals = {}

    originals[
        "forgecad.adapters.freecad.joint_status_adapter"
    ] = install_fake_module(
        "forgecad.adapters.freecad.joint_status_adapter",
        joint_review_for_document=(
            lambda current_document: review
        ),
    )

    originals[
        "forgecad.services.joint_constraints"
    ] = install_fake_module(
        "forgecad.services.joint_constraints",
        collinear_through_constraint_for_joint=(
            lambda joint: (
                constraint_a
                if joint is joint_a
                else None
            )
        ),
    )

    originals[
        "forgecad.adapters.freecad.joint_constraint_store"
    ] = install_fake_module(
        "forgecad.adapters.freecad.joint_constraint_store",
        constraint_objects=(
            lambda current_document: tuple(
                existing
            )
        ),
        save_joint_constraint=(
            lambda current_document,
            node_key,
            constraint: (
                saved.append(
                    (
                        node_key,
                        constraint,
                    )
                )
                or FakeConstraintObject(
                    node_key
                )
            )
        ),
        remove_joint_constraint=(
            lambda current_document,
            node_key: (
                removed.append(
                    node_key
                )
                or True
            )
        ),
    )

    try:
        result = (
            module.synchronize_joint_constraints(
                document
            )
        )

    finally:
        for name, original in originals.items():
            restore_module(
                name,
                original,
            )

    assert saved == [
        (
            "A",
            constraint_a,
        )
    ]

    assert removed == [
        "STALE"
    ]

    assert len(
        result
    ) == 1

    assert result[0].NodeKey == "A"


def test_refresh_rebuilds_markers_before_synchronizing_constraints():
    document = object()

    events = []

    fake_status_name = (
        "forgecad.adapters.freecad.joint_status_objects"
    )

    original_status = install_fake_module(
        fake_status_name,
        rebuild_joint_status_objects=(
            lambda current_document: (
                events.append(
                    "markers"
                )
                or (
                    "J001",
                )
            )
        ),
    )

    original_sync = (
        module.synchronize_joint_constraints
    )

    module.synchronize_joint_constraints = (
        lambda current_document: (
            events.append(
                "constraints"
            )
            or (
                "C001",
            )
        )
    )

    try:
        result = (
            module.refresh_joint_topology(
                document
            )
        )

    finally:
        module.synchronize_joint_constraints = (
            original_sync
        )

        restore_module(
            fake_status_name,
            original_status,
        )

    assert events == [
        "markers",
        "constraints",
    ]

    assert result == (
        (
            "J001",
        ),
        (
            "C001",
        ),
    )
