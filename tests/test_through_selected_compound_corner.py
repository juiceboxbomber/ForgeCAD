"""Regression tests for compound selection-first Through corners."""

import ast
import sys
import types
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "forgecad/adapters/freecad/renderer.py"


def _load_renderer_function(monkeypatch, pairs):
    text = RENDERER.read_text(encoding="utf-8")
    tree = ast.parse(text)
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "explicit_through_cope_specifications_for_joint"
    ]
    assert len(matches) == 1

    module = ast.Module(body=[matches[0]], type_ignores=[])
    ast.fix_missing_locations(module)

    store = types.ModuleType(
        "forgecad.adapters.freecad.joint_treatment_store"
    )
    store.load_joint_through_pairs = lambda document, key: tuple(pairs)
    monkeypatch.setitem(
        sys.modules,
        "forgecad.adapters.freecad.joint_treatment_store",
        store,
    )

    fabrication = types.ModuleType("forgecad.fabrication")

    class FakeJoint:
        def __init__(self, node, members):
            self.node = node
            self.members = tuple(members)

    fabrication.Joint = FakeJoint
    monkeypatch.setitem(sys.modules, "forgecad.fabrication", fabrication)

    resolver = types.ModuleType(
        "forgecad.services.joint_treatment_resolver"
    )

    def member_through_cope_instructions(joint, through_member, branch_members):
        branch_members = tuple(branch_members)
        result = [
            SimpleNamespace(
                joint=joint,
                coped_member=branch,
                target_member=through_member,
            )
            for branch in branch_members
        ]
        if len(branch_members) == 2:
            result.append(
                SimpleNamespace(
                    joint=joint,
                    coped_member=branch_members[1],
                    target_member=branch_members[0],
                )
            )
        return tuple(result)

    resolver.member_through_cope_instructions = (
        member_through_cope_instructions
    )
    monkeypatch.setitem(
        sys.modules,
        "forgecad.services.joint_treatment_resolver",
        resolver,
    )

    notch = types.ModuleType("forgecad.services.notch_analysis")
    notch.build_cope_specification = lambda instruction: (
        instruction.coped_member.name,
        instruction.target_member.name,
    )
    monkeypatch.setitem(
        sys.modules,
        "forgecad.services.notch_analysis",
        notch,
    )

    members = {
        name: SimpleNamespace(name=name)
        for name in (
            "upright",
            "base_a",
            "base_b",
            "base_c",
        )
    }

    namespace = {
        "node_key": lambda node: "corner",
        "member_for_layout_id": (
            lambda joint, layout_id, mapping: members.get(layout_id)
        ),
    }
    exec(
        compile(module, str(RENDERER), "exec"),
        namespace,
    )
    return (
        namespace["explicit_through_cope_specifications_for_joint"],
        members,
    )


def test_two_sequential_corner_branches_get_secondary_branch_cope(monkeypatch):
    function, members = _load_renderer_function(
        monkeypatch,
        (
            ("base_a", "upright"),
            ("base_b", "upright"),
        ),
    )
    joint = SimpleNamespace(
        node=object(),
        members=tuple(members.values()),
    )
    result = function(None, joint, {})
    assert result == (
        ("base_a", "upright"),
        ("base_b", "upright"),
        ("base_b", "base_a"),
    )


def test_one_branch_remains_a_simple_branch_to_through_cope(monkeypatch):
    function, members = _load_renderer_function(
        monkeypatch,
        (("base_a", "upright"),),
    )
    joint = SimpleNamespace(
        node=object(),
        members=tuple(members.values()),
    )
    assert function(None, joint, {}) == (
        ("base_a", "upright"),
    )


def test_three_branches_do_not_invent_secondary_pairing(monkeypatch):
    function, members = _load_renderer_function(
        monkeypatch,
        (
            ("base_a", "upright"),
            ("base_b", "upright"),
            ("base_c", "upright"),
        ),
    )
    joint = SimpleNamespace(
        node=object(),
        members=tuple(members.values()),
    )
    assert function(None, joint, {}) == (
        ("base_a", "upright"),
        ("base_b", "upright"),
        ("base_c", "upright"),
    )
