"""Tests for persistent multi-joint bent-tube topology."""

import sys
import types


class FakeVector:
    def __init__(
        self,
        x,
        y,
        z,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


fake_freecad = types.ModuleType(
    "FreeCAD"
)
fake_freecad.Vector = FakeVector

fake_part = types.ModuleType(
    "Part"
)

sys.modules[
    "FreeCAD"
] = fake_freecad
sys.modules[
    "Part"
] = fake_part


from forgecad.adapters.freecad.bent_tube_object import (
    ensure_bent_tube_design_joint_links,
)


class FakeObject:
    """Minimal FreeCAD object supporting dynamic properties."""

    def __init__(
        self,
    ):
        self.added_properties = []

    def addProperty(
        self,
        property_type,
        property_name,
        group,
    ):
        self.added_properties.append(
            (
                property_type,
                property_name,
                group,
            )
        )

        setattr(
            self,
            property_name,
            None,
        )


def _node(
    x,
    y,
    z,
):
    return types.SimpleNamespace(
        Position=FakeVector(
            x,
            y,
            z,
        )
    )


def test_single_design_joint_uses_numbered_joint_link():
    """
    A one-bend tube stores its theoretical corner as DesignJointNode1.

    Keeping joint links numbered gives the topology a natural extension
    path when additional bends are added later.
    """

    obj = FakeObject()

    joint = _node(
        1000.0,
        0.0,
        0.0,
    )

    result = (
        ensure_bent_tube_design_joint_links(
            obj,
            (
                joint,
            ),
        )
    )

    assert result is obj

    assert (
        obj.DesignJointNode1
        is joint
    )

    assert (
        "App::PropertyLink",
        "DesignJointNode1",
        "ForgeCAD Topology",
    ) in obj.added_properties


def test_two_bend_tube_stores_two_design_joint_links():
    """
    A two-bend continuous tube has two theoretical design corners.
    """

    obj = FakeObject()

    first_joint = _node(
        1000.0,
        0.0,
        0.0,
    )

    second_joint = _node(
        1000.0,
        1000.0,
        0.0,
    )

    ensure_bent_tube_design_joint_links(
        obj,
        (
            first_joint,
            second_joint,
        ),
    )

    assert (
        obj.DesignJointNode1
        is first_joint
    )

    assert (
        obj.DesignJointNode2
        is second_joint
    )


def test_existing_design_joint_links_are_reused():
    """
    Extending a bent tube must preserve its existing first design joint.
    """

    obj = FakeObject()

    first_joint = _node(
        1000.0,
        0.0,
        0.0,
    )

    second_joint = _node(
        1000.0,
        1000.0,
        0.0,
    )

    ensure_bent_tube_design_joint_links(
        obj,
        (
            first_joint,
        ),
    )

    initial_property_count = len(
        obj.added_properties
    )

    ensure_bent_tube_design_joint_links(
        obj,
        (
            first_joint,
            second_joint,
        ),
    )

    assert (
        obj.DesignJointNode1
        is first_joint
    )

    assert (
        obj.DesignJointNode2
        is second_joint
    )

    assert len(
        obj.added_properties
    ) == (
        initial_property_count + 1
    )


def test_legacy_design_joint_link_is_migrated_to_first_numbered_link():
    """
    Existing one-bend documents currently use DesignJointNode.

    Multi-bend support must preserve that topology instead of requiring
    old documents to be recreated.
    """

    obj = FakeObject()

    legacy_joint = _node(
        1000.0,
        0.0,
        0.0,
    )

    obj.DesignJointNode = (
        legacy_joint
    )

    ensure_bent_tube_design_joint_links(
        obj,
        ()
    )

    assert (
        obj.DesignJointNode1
        is legacy_joint
    )


def test_design_joint_links_are_returned_in_path_order():
    """
    Joint links must remain ordered from StartNode toward EndNode.
    """

    obj = FakeObject()

    first_joint = _node(
        1000.0,
        0.0,
        0.0,
    )

    second_joint = _node(
        1000.0,
        1000.0,
        0.0,
    )

    result = (
        ensure_bent_tube_design_joint_links(
            obj,
            (
                first_joint,
                second_joint,
            ),
        )
    )

    assert (
        result.DesignJointNode1,
        result.DesignJointNode2,
    ) == (
        first_joint,
        second_joint,
    )
    