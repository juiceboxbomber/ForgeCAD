"""Regression coverage for straight + bent tube cut-list collection."""

import ast
import math
from pathlib import Path
from types import SimpleNamespace

from forgecad.services import (
    create_default_material,
    create_default_tube_library,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = (
    ROOT
    / "forgecad"
    / "adapters"
    / "freecad"
    / "commands"
    / "cut_list.py"
)


def _function_source(name):
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef)
        and item.name == name
    )
    return ast.get_source_segment(source, node)


def _namespace():
    namespace = {
        "math": math,
        "create_default_material": create_default_material,
        "create_default_tube_library": create_default_tube_library,
    }

    for name in (
        "member_weight_kg",
        "frame_member_objects",
        "cut_list_rows",
    ):
        exec(_function_source(name), namespace)

    return namespace


class FakeGroup:
    def __init__(self, objects=()):
        self.Group = list(objects)


class FakeDocument:
    def __init__(self, frame=(), bent=()):
        self.groups = {
            "ForgeCADFrame": FakeGroup(frame),
            "ForgeCADBentTubes": FakeGroup(bent),
        }

    def getObject(self, name):
        return self.groups.get(name)


def _straight():
    return SimpleNamespace(
        Name="ForgeCADMember001",
        MemberID="M001",
        MemberName="Side Rail",
        TubeProfile="1.500 x .120 DOM",
        MemberLength=1000.0,
        Material="A513 Type 5 DOM",
    )


def _bent():
    return SimpleNamespace(
        Name="ForgeCADBentTube",
        TubeName="Main Hoop",
        TubeProfile="2.000 x .120 DOM",
        DevelopedLength=1350.0,
        Material="A513 Type 5 DOM",
    )


def test_cut_list_collects_straight_and_bent_groups():
    namespace = _namespace()
    straight = _straight()
    bent = _bent()

    result = namespace["frame_member_objects"](
        FakeDocument(
            frame=(straight,),
            bent=(bent,),
        )
    )

    assert result == [straight, bent]


def test_cut_list_rows_include_bent_developed_length():
    namespace = _namespace()

    rows = namespace["cut_list_rows"](
        FakeDocument(
            frame=(_straight(),),
            bent=(_bent(),),
        )
    )

    assert len(rows) == 2

    straight_row = rows[0]
    bent_row = rows[1]

    assert straight_row["member_id"] == "M001"
    assert straight_row["tube_profile"] == "1.500 x .120 DOM"
    assert straight_row["length_mm"] == 1000.0

    assert bent_row["member_id"] == "ForgeCADBentTube"
    assert bent_row["member_name"] == "Main Hoop"
    assert bent_row["tube_profile"] == "2.000 x .120 DOM"
    assert bent_row["length_mm"] == 1350.0
    assert bent_row["weight_kg"] > 0.0


def test_cut_list_can_work_with_only_bent_tubes():
    namespace = _namespace()

    document = FakeDocument(
        frame=(),
        bent=(_bent(),),
    )
    document.groups["ForgeCADFrame"] = None

    rows = namespace["cut_list_rows"](document)

    assert len(rows) == 1
    assert rows[0]["member_name"] == "Main Hoop"